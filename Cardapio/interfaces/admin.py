from django.contrib import admin
from django.http import JsonResponse
from django.utils import timezone
from django.urls import path
from .models import Restaurante, ItemCardapio, Pedido, ItemPedido
from datetime import timedelta

MINUTOS_ATE_SUMIR = 1

admin.site.register(Restaurante)
admin.site.register(ItemCardapio)

#Classes de customização e lógica dos pedidos
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('item_cardapio', 'quantidade', 'preco_unitario')
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):

    list_display = ('id', 'mesa', 'restaurante', 'status', 'criado_em', 'proxima_acao')
    list_filter = ('status',)
    ordering = ('criado_em',)
    readonly_fields = ('restaurante', 'mesa', 'criado_em')
    inlines = [ItemPedidoInline]

    class Media:
        css = {
            'all': ('cardapio/css/pedidos.css',)
        }
        js = ('cardapio/js/pedidos.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            if obj.status == Pedido.Status.PAGO:
                # Se está PAGO, só pode avançar para EM PREPARO
                form.base_fields['status'].choices = [
                    (Pedido.Status.PAGO, 'Pago'),
                    (Pedido.Status.EM_PREPARO, 'Em Preparo'),
                ]
            elif obj.status == Pedido.Status.EM_PREPARO:
                # Se está EM PREPARO, só pode avançar para PRONTO
                form.base_fields['status'].choices = [
                    (Pedido.Status.EM_PREPARO, 'Em Preparo'),
                    (Pedido.Status.PRONTO, 'Pronto'),
                ]
        return form
        # Coluna extra que mostra o próximo passo de forma clara para o garçom

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
        queryset.filter(status=Pedido.Status.EM_PREPARO).update(
            status=Pedido.Status.PRONTO
        )

    actions = ['marcar_em_preparo', 'marcar_pronto']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pedidos-ativos/', self.admin_site.admin_view(self.pedidos_ativos_json),
                 name='pedidos_ativos_json'),
        ]
        return custom_urls + urls

    def pedidos_ativos_json(self, request):
        HORAS_ATE_ARQUIVAR = 24
        limite_arquivar = timezone.now() - timedelta(hours=HORAS_ATE_ARQUIVAR)

        pedidos = Pedido.objects.exclude(
            status=Pedido.Status.PRONTO,
            pronto_em__lt=limite_arquivar
        ).order_by('criado_em')

        dados = []
        for pedido in pedidos:
            segundos_restantes = None
            if pedido.status == Pedido.Status.PRONTO and pedido.pronto_em:
                segundos_passados = (timezone.now() - pedido.pronto_em).total_seconds()
                restantes = (MINUTOS_ATE_SUMIR * 60) - segundos_passados
                segundos_restantes = restantes if restantes > 0 else None

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