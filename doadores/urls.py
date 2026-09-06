from django.urls import path

from . import views

app_name = 'doadores'

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel/', views.painel, name='painel'),
    path('painel/editar/', views.editar, name='editar'),
    path('agendar/<int:hemocentro_id>/', views.criar_agendamento, name='criar_agendamento'),
    path('agendamento/<int:agendamento_id>/cancelar/', views.cancelar_agendamento, name='cancelar_agendamento'),
    path('api/hemocentro/<int:hemocentro_id>/dados-agendamento/', views.dados_agendamento_hemocentro, name='dados_agendamento_hemocentro'),
]
