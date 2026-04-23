from django.urls import path
from . import view

urlpatterns = [
    path('', view.cardapioHome),
    path('adicionar/', view.cardapioItem),
]