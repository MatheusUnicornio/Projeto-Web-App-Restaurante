from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

# A URL terá o id do restaurante e o número da mesa, ex: /cardapio/1/mesa/3/
# get_object_or_404 vai retornar erro 404 automaticamente se o restaurante não existir.
def cardapio(request, restaurante_id, mesa):
    restaurante = get_object_or_404(Restaurante, pk=restaurante_id, ativo=True)

    # Busca só os itens disponíveis do restaurante específico
    itens = ItemCardapio.objects.filter(restaurante=restaurante, disponivel=True)

    context = {
        'restaurante': restaurante,
        'itens': itens,
        'mesa': mesa,
    }
    return render(request, 'cardapio/cardapio.html', context)