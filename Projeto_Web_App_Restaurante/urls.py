from django.contrib import admin
from django.urls import path, include
from . import view
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('cardapio/', include('Cardapio.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #Serve as fotos dos pratos em desenvolvimento
