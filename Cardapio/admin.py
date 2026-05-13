from django.contrib import admin
from .models import Restaurante, ItemCardapio, Pedido, ItemPedido

admin.site.register(Restaurante)
admin.site.register(ItemCardapio)
admin.site.register(Pedido)
admin.site.register(ItemPedido)