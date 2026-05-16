from django.db import models
import mercadopago
import os
from Cardapio.domain.models import Pedido, ItemPedido
from groq import Groq
from Cardapio.domain.models import ItemCardapio

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
#
#
#LÓGICA IMPLEMENTAÇÃO DA IA
#
#
def responder_chatbot(mensagem: str, restaurante) -> str:
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    itens = ItemCardapio.objects.filter(restaurante=restaurante, disponivel=True)

    cardapio_texto = '\n'.join([
        f"- {item.nome}: R${item.preco} | {item.descricao} | Restrições: {item.restricoes or 'nenhuma'}"
        for item in itens
    ])

    system_prompt = f"""Você é um assistente simpático do restaurante {restaurante.nome}.
    Seu papel é ajudar os clientes com dúvidas sobre o cardápio, fazer recomendações
    e responder perguntas sobre os pratos. Seja conciso e amigável.

    Cardápio atual:
    {cardapio_texto}

    Regras:
    - Responda sempre em português
    - Seja breve — máximo 3 frases por resposta
    - Se perguntarem algo fora do cardápio, redirecione gentilmente para os pratos
    - Não invente pratos ou preços que não estão no cardápio acima
    """

    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': mensagem},
        ],
        max_tokens=200,
        temperature=0.7,
    )

    return response.choices[0].message.content