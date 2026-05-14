from django.contrib import admin
from .models import Restaurante, ItemCardapio, Pedido, ItemPedido

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