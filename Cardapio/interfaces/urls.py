from django.urls import path
from . import view

#Link que vai ser codificado no QR Code de cada mesa.
urlpatterns = [
    path('<int:restaurante_id>/mesa/<int:mesa>/',
         view.cardapio, name='cardapio'),
    path('<int:restaurante_id>/mesa/<int:mesa>/adicionar/<int:item_id>/',
         view.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),

    path('<int:restaurante_id>/mesa/<int:mesa>/remover/<int:item_id>/',
         view.remover_do_carrinho, name='remover_do_carrinho'),

    path('<int:restaurante_id>/mesa/<int:mesa>/confirmar/',
         view.confirmar_pedido, name='confirmar_pedido'),

    path('pagamento/sucesso/', view.pagamento_sucesso, name='pagamento_sucesso'),
    path('pagamento/falha/', view.pagamento_falha, name='pagamento_falha'),
    path('pagamento/pendente/', view.pagamento_pendente, name='pagamento_pendente'),

    path('pagamento/webhook/',  view.webhook_pagamento,  name='webhook_pagamento'),

    path('<int:restaurante_id>/chat/', view.chatbot, name='chatbot'),
]