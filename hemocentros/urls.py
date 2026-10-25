from django.urls import path

from . import views

app_name = 'hemocentros'

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel/', views.painel, name='painel'),
    path('painel/editar/', views.editar, name='editar'),
    path('painel/estoque/', views.atualizar_estoque, name='atualizar_estoque'),
    path('painel/estoque/alerta/', views.emitir_alerta_estoque, name='emitir_alerta_estoque'),
    path('painel/doadores/novo/', views.cadastrar_doador_presencial, name='cadastrar_doador_presencial'),
    path('painel/registrar-doacao/', views.registrar_doacao, name='registrar_doacao'),
    path('painel/agendamento/<int:agendamento_id>/status/', views.atualizar_agendamento, name='atualizar_agendamento'),
]
