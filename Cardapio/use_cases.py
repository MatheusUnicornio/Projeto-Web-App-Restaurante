from django.db import models
import mercadopago
import os
from .models import Pedido, ItemPedido, ItemCardapio


#LÓGICA DO CARRINHO
def adicionar_item(carrinho: dict, item_id: int, nome: str, preco: float) -> dict:
    chave = str(item_id)

    if chave in carrinho:
        carrinho[chave]['quantidade'] += 1
    else:
        carrinho[chave] = {
            'nome': nome,
            'preco': preco,
            'quantidade': 1,
        }

    return carrinho


def remover_item(carrinho: dict, item_id: int) -> dict:
   chave = str(item_id)

   if chave not in carrinho:
       return carrinho

   if carrinho[chave]['quantidade'] > 1:
       carrinho[chave]['quantidade'] -= 1
   else:
       del carrinho[chave]

   return carrinho


def calcular_total(carrinho: dict) -> float:
   total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
   return round(total, 2)

def criar_pedido(carrinho: dict, restaurante, mesa: int):
    pedido = Pedido.objects.create(
        restaurante=restaurante,
        mesa=mesa,
        status=Pedido.Status.AGUARDANDO_PAGAMENTO,
    )

    for chave, dados in carrinho.items():
        item_cardapio = ItemCardapio.objects.get(pk=int(chave))
        ItemPedido.objects.create(
            pedido=pedido,
            item_cardapio=item_cardapio,
            quantidade=dados['quantidade'],
            preco_unitario=dados['preco'],
        )

    return pedido

#LÓGICA DE PAGAMENTO
def _montar_itens_pagamento(pedido) -> list:
    items = []
    for item_pedido in pedido.itens.all():
        items.append({
            'title': item_pedido.item_cardapio.nome,
            'quantity': item_pedido.quantidade,
            'unit_price': float(item_pedido.preco_unitario),
            'currency_id': 'BRL',
        })
    return items


def _montar_preference_data(pedido, base_url: str) -> dict:
    return {
        'items': _montar_itens_pagamento(pedido),
        'external_reference': str(pedido.id),
        'back_urls': {
            'success': f'{base_url}/cardapio/pagamento/sucesso/',
            'failure': f'{base_url}/cardapio/pagamento/falha/',
            'pending': f'{base_url}/cardapio/pagamento/pendente/',
        },
    }


def gerar_pagamento(pedido, request) -> str:
    sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))
    base_url = request.build_absolute_uri('/').rstrip('/')
    preference_data = _montar_preference_data(pedido, base_url)
    result = sdk.preference().create(preference_data)
    preference = result['response']
    return preference.get('sandbox_init_point') or preference.get('init_point')