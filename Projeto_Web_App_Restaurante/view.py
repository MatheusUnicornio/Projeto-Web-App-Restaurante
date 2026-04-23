from django.http import HttpResponse

def testeView(request):
    return HttpResponse("<h1>Bah!!!</h1><br><br><br>")

def indexView(request):
    return HttpResponse("<h1>huehuehue</h1>")   