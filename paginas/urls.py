from django.urls import path

from . import views

app_name = 'paginas'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('api/mapa/', views.dados_mapa, name='dados_mapa'),
]
