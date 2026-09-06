from django.urls import path

from . import views

app_name = 'hemocentros'

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel/', views.painel, name='painel'),
    path('painel/editar/', views.editar, name='editar'),
    path('painel/registrar-doacao/', views.registrar_doacao, name='registrar_doacao'),
    path('painel/agendamento/<int:agendamento_id>/status/', views.atualizar_agendamento, name='atualizar_agendamento'),
]
