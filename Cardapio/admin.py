from django.contrib import admin
from django.http import JsonResponse
from django.utils import timezone
from django.urls import path
from datetime import timedelta
from Cardapio.domain.models import Restaurante, ItemCardapio, Pedido, ItemPedido


MINUTOS_ATE_SUMIR = 1
HORAS_ATE_ARQUIVAR = 24



class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('item_cardapio', 'quantidade', 'preco_unitario')
    extra = 0


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):

    def has_module_perms(self, request, app_label):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser


@admin.register(ItemCardapio)
class ItemCardapioAdmin(admin.ModelAdmin):

    def has_module_perms(self, request, app_label):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'restaurante', 'status', 'criado_em', 'proxima_acao')
    list_filter = ('status',)
    ordering = ('criado_em',)
    readonly_fields = ('restaurante', 'mesa', 'criado_em', 'pronto_em')
    inlines = [ItemPedidoInline]

    class Media:
        css = {'all': ('cardapio/css/pedidos.css',)}
        js = ('cardapio/js/pedidos.js',)

    def has_module_perms(self, request, app_label):
        return (
                request.user.groups.filter(name__in=['Gerência', 'Atendente']).exists()
                or request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return (
                request.user.groups.filter(name__in=['Gerência', 'Atendente']).exists()
                or request.user.is_superuser
        )

    def has_change_permission(self, request, obj=None):
        return (
                request.user.groups.filter(name__in=['Gerência', 'Atendente']).exists()
                or request.user.is_superuser
        )

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Gerência').exists() or request.user.is_superuser

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            if obj.status == Pedido.Status.PAGO:
                form.base_fields['status'].choices = [
                    (Pedido.Status.PAGO, 'Pago'),
                    (Pedido.Status.EM_PREPARO, 'Em Preparo'),
                ]
            elif obj.status == Pedido.Status.EM_PREPARO:
                form.base_fields['status'].choices = [
                    (Pedido.Status.EM_PREPARO, 'Em Preparo'),
                    (Pedido.Status.PRONTO, 'Pronto'),
                ]
        return form

    @admin.display(description='Próxima Ação')
    def proxima_acao(self, obj):
        if obj.status == Pedido.Status.PAGO:
            return '👨‍🍳 Iniciar preparo'
        elif obj.status == Pedido.Status.EM_PREPARO:
            return '✅ Marcar como pronto'
        elif obj.status == Pedido.Status.PRONTO:
            return '🎉 Entregar na mesa'
        return '⏳ Aguardando pagamento'

    @admin.action(description='Marcar selecionados como Em Preparo')
    def marcar_em_preparo(self, request, queryset):
        queryset.filter(status=Pedido.Status.PAGO).update(
            status=Pedido.Status.EM_PREPARO
        )

    @admin.action(description='Marcar selecionados como Prontos')
    def marcar_pronto(self, request, queryset):
        for pedido in queryset.filter(status=Pedido.Status.EM_PREPARO):
            pedido.status = Pedido.Status.PRONTO
            pedido.save()

    actions = ['marcar_em_preparo', 'marcar_pronto']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pedidos-ativos/', self.admin_site.admin_view(self.pedidos_ativos_json),
                 name='pedidos_ativos_json'),
        ]
        return custom_urls + urls

    def pedidos_ativos_json(self, request):
        limite_arquivar = timezone.now() - timedelta(hours=HORAS_ATE_ARQUIVAR)

        pedidos = Pedido.objects.exclude(
            status=Pedido.Status.PRONTO,
            pronto_em__lt=limite_arquivar
        ).order_by('criado_em')

        dados = []
        for pedido in pedidos:
            segundos_restantes = self._calcular_segundos_restantes(pedido)
            dados.append({
                'id': pedido.id,
                'mesa': pedido.mesa,
                'restaurante': str(pedido.restaurante),
                'status': pedido.get_status_display(),
                'criado_em': pedido.criado_em.strftime('%H:%M'),
                'segundos_restantes': segundos_restantes,
                'proxima_acao': self.proxima_acao(pedido),
                'url': f'/admin/Cardapio/pedido/{pedido.id}/change/',
            })

        return JsonResponse({'pedidos': dados})

    def _calcular_segundos_restantes(self, pedido):
        if pedido.status != Pedido.Status.PRONTO or not pedido.pronto_em:
            return None
        segundos_passados = (timezone.now() - pedido.pronto_em).total_seconds()
        restantes = (MINUTOS_ATE_SUMIR * 60) - segundos_passados
        return restantes if restantes > 0 else None