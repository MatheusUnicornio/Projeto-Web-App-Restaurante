from django.urls import path
from . import view


urlpatterns = [
    path('<int:restaurante_id>/mesa/<int:mesa>/', views.cardapio, name='cardapio'),
]