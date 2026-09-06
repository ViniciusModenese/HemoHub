from django.urls import path

from . import views

app_name = 'necessidades'

urlpatterns = [
    path('criar/', views.criar, name='criar'),
    path('<int:pk>/encerrar/', views.encerrar, name='encerrar'),
    path('notificacoes/<int:pk>/ir/', views.abrir_notificacao, name='abrir_notificacao'),
]
