#Lógica do Carrinho
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
    from .models import Pedido, ItemPedido, ItemCardapio

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