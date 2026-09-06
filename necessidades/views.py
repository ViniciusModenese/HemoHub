from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from doadores.models import Doador
from hemocentros.models import Hemocentro

from .forms import FormularioNecessidade
from .models import NecessidadeSanguinea, NotificacaoDoador
from .servicos import buscar_doadores_compativeis_proximos


@login_required
def criar(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    if request.method == 'POST':
        formulario = FormularioNecessidade(request.POST)
        if formulario.is_valid():
            necessidade = formulario.save(commit=False)
            necessidade.hemocentro = hemocentro
            quantidade_notificados = len(buscar_doadores_compativeis_proximos(necessidade)) if necessidade.deve_notificar else None
            necessidade.save()
            if quantidade_notificados is not None:
                messages.success(request, f'Necessidade registrada. {quantidade_notificados} doador(es) próximo(s) compatível(is) notificado(s) por e-mail.')
            else:
                messages.success(request, 'Necessidade registrada com sucesso.')
            return redirect('hemocentros:painel')
    else:
        formulario = FormularioNecessidade()
    return render(request, 'necessidades/criar.html', {'formulario': formulario})


@login_required
@require_POST
def encerrar(request, pk):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    necessidade = get_object_or_404(NecessidadeSanguinea, pk=pk, hemocentro=hemocentro)
    necessidade.ativa = False
    necessidade.save()
    messages.success(request, 'Necessidade encerrada.')
    return redirect('hemocentros:painel')


@login_required
def abrir_notificacao(request, pk):
    doador = get_object_or_404(Doador, usuario=request.user)
    notificacao = get_object_or_404(NotificacaoDoador, pk=pk, doador=doador)
    notificacao.lida = True
    notificacao.save()
    url_mapa = reverse('paginas:inicio')
    return redirect(f'{url_mapa}?hemocentro={notificacao.necessidade.hemocentro_id}')
