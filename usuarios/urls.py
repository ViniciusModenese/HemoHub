from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.TelaLogin.as_view(), name='login'),
    path('logout/', views.TelaLogout.as_view(), name='logout'),
    path('painel/', views.redirecionar_painel, name='redirecionar_painel'),
]
