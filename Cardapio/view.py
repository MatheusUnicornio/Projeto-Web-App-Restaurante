from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Restaurante, ItemCardapio, Pedido
from . import use_cases
import json

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

    url_pagamento = use_cases.gerar_pagamento(pedido, request)
    return redirect(url_pagamento)

def pagamento_sucesso(request):
    #print('GET PARAMS:', request.GET)
    #print('GET DICT:', dict(request.GET))
    pedido_id = dict(request.GET).get('external_reference', [None])[0]
    #print('PEDIDO ID RECEBIDO:', pedido_id)
    #print('TIPO:', type(pedido_id))
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    pedido.status = Pedido.Status.PAGO
    pedido.save()

    return render(request, 'cardapio/pedido_confirmado.html', {
        'pedido': pedido,
        'mesa': pedido.mesa,
        'restaurante_id': pedido.restaurante_id,
    })

def pagamento_falha(request):
    return render(request, 'cardapio/pagamento_falha.html')


def pagamento_pendente(request):
    return render(request, 'cardapio/pagamento_pendente.html')


@csrf_exempt  # desativa proteção CSRF pois o Mercado Pago não envia o token
def webhook_pagamento(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)

        # O Mercado Pago envia tipo 'payment' quando um pagamento é processado
        if data.get('type') == 'payment':
            import mercadopago
            import os

            sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))
            payment_id = data['data']['id']

            # Busca os detalhes do pagamento na API do Mercado Pago
            payment = sdk.payment().get(payment_id)
            payment_data = payment['response']

            pedido_id = payment_data.get('external_reference')
            status_mp = payment_data.get('status')

            pedido = Pedido.objects.get(pk=pedido_id)

            if status_mp == 'approved':
                pedido.status = Pedido.Status.PAGO
            elif status_mp in ['rejected', 'cancelled']:
                pedido.status = Pedido.Status.AGUARDANDO_PAGAMENTO

            pedido.save()

    except Exception:
        pass

    return HttpResponse(status=200)
