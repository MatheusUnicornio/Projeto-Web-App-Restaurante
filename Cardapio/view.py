from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Restaurante, ItemCardapio
from . import use_cases

# A URL terá o id do restaurante e o número da mesa, ex: /cardapio/1/mesa/3/
# get_object_or_404 vai retornar erro 404 automaticamente se o restaurante não existir.
def cardapio(request, restaurante_id, mesa):
    restaurante = get_object_or_404(Restaurante, pk=restaurante_id, ativo=True)
    itens = ItemCardapio.objects.filter(restaurante=restaurante, disponivel=True)
    carrinho = request.session.get('carrinho', {})
    total = use_cases.calcular_total(carrinho)

    context = {
        'restaurante': restaurante,
        'itens': itens,
        'mesa': mesa,
        'carrinho': carrinho,
        'total': total,
    }
    return render(request, 'cardapio/cardapio.html', context)

def adicionar_ao_carrinho(request, restaurante_id, mesa, item_id):
    item = get_object_or_404(ItemCardapio, pk=item_id)
    carrinho = request.session.get('carrinho', {})
    carrinho = use_cases.adicionar_item(carrinho, item_id, item.nome, float(item.preco))
    request.session['carrinho'] = carrinho
    return redirect('cardapio', restaurante_id=restaurante_id, mesa=mesa)


def remover_do_carrinho(request, restaurante_id, mesa, item_id):
    carrinho = request.session.get('carrinho', {})
    carrinho = use_cases.remover_item(carrinho, item_id)
    request.session['carrinho'] = carrinho
    return redirect('cardapio', restaurante_id=restaurante_id, mesa=mesa)


def confirmar_pedido(request, restaurante_id, mesa):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('cardapio', restaurante_id=restaurante_id, mesa=mesa)

    restaurante = get_object_or_404(Restaurante, pk=restaurante_id)
    pedido = use_cases.criar_pedido(carrinho, restaurante, mesa)
    request.session['carrinho'] = {}

    return render(request, 'cardapio/pedido_confirmado.html', {
        'pedido': pedido,
        'mesa': mesa,
        'restaurante_id': restaurante_id,
    })

