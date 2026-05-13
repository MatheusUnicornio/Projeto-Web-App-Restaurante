from django.urls import path
from . import view

#Link que vai ser codificado no QR Code de cada mesa.
urlpatterns = [
    path('<int:restaurante_id>/mesa/<int:mesa>/', view.cardapio, name='cardapio'),
]