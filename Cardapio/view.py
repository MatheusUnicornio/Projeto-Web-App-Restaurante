from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def cardapioHome(request):
    return render(request, 'testeHtml/home.html')
def cardapioItem(request):
    return HttpResponse("Seu item a adicionar: ")