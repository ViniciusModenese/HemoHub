from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from doadores.forms import FormularioHistoricoDoacao
from doadores.models import Agendamento, Doador, HistoricoDoacao
from usuarios.models import Usuario

from .forms import FormularioCadastroHemocentro, FormularioEditarHemocentro
from .models import FotoHemocentro, Hemocentro

CAMPOS_ENDERECO = ('logradouro', 'numero', 'bairro', 'cidade', 'estado')


def cadastro(request):
    if request.method == 'POST':
        formulario = FormularioCadastroHemocentro(request.POST)
        if formulario.is_valid():
            dados = formulario.cleaned_data
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
                    username=dados['username'],
                    email=dados['email'],
                    password=dados['password1'],
                    tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO,
                )
                hemocentro = Hemocentro.objects.create(
                    usuario=usuario,
                    nome=dados['nome'],
                    cnpj=dados['cnpj'],
                    descricao=dados['descricao'],
                    telefone=dados['telefone'],
                    horario_funcionamento=dados['horario_funcionamento'],
                    logradouro=dados['logradouro'],
                    numero=dados['numero'],
                    bairro=dados['bairro'],
                    cidade=dados['cidade'],
                    estado=dados['estado'],
                    cep=dados['cep'],
                )
                for arquivo in request.FILES.getlist('fotos'):
                    FotoHemocentro.objects.create(hemocentro=hemocentro, imagem=arquivo)
            login(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('hemocentros:painel')
    else:
        formulario = FormularioCadastroHemocentro()
    return render(request, 'hemocentros/cadastro.html', {'formulario': formulario})


@login_required
def painel(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    necessidades = hemocentro.necessidades.all()
    agendamentos = hemocentro.agendamentos.select_related('doador').order_by('data', 'horario')
    return render(request, 'hemocentros/painel.html', {
        'hemocentro': hemocentro,
        'necessidades': necessidades,
        'agendamentos': agendamentos,
    })


@login_required
def atualizar_agendamento(request, agendamento_id):
    if request.method != 'POST':
        return redirect('hemocentros:painel')
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    agendamento = get_object_or_404(Agendamento, pk=agendamento_id, hemocentro=hemocentro)
    acao = request.POST.get('acao')
    if acao == 'concluir':
        agendamento.status = Agendamento.Status.CONCLUIDO
        agendamento.save()
        HistoricoDoacao.objects.create(
            doador=agendamento.doador,
            data_doacao=agendamento.data,
            local=hemocentro.nome,
        )
        messages.success(request, f'Doação de {agendamento.doador.nome_completo} confirmada e registrada com sucesso!')
    elif acao == 'cancelar':
        agendamento.status = Agendamento.Status.CANCELADO
        agendamento.save()
        messages.info(request, f'Agendamento de {agendamento.doador.nome_completo} cancelado.')
    return redirect('hemocentros:painel')


@login_required
def editar(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    if request.method == 'POST':
        formulario = FormularioEditarHemocentro(request.POST, instance=hemocentro)
        if formulario.is_valid():
            endereco_antigo = tuple(getattr(hemocentro, campo) for campo in CAMPOS_ENDERECO)
            hemocentro_atualizado = formulario.save(commit=False)
            endereco_novo = tuple(getattr(hemocentro_atualizado, campo) for campo in CAMPOS_ENDERECO)
            if endereco_novo != endereco_antigo:
                hemocentro_atualizado.latitude = None
                hemocentro_atualizado.longitude = None
            hemocentro_atualizado.save()
            for arquivo in request.FILES.getlist('fotos'):
                FotoHemocentro.objects.create(hemocentro=hemocentro_atualizado, imagem=arquivo)
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('hemocentros:painel')
    else:
        formulario = FormularioEditarHemocentro(instance=hemocentro)
    return render(request, 'hemocentros/editar.html', {'formulario': formulario, 'hemocentro': hemocentro})


@login_required
def registrar_doacao(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)

    if request.method == 'POST':
        doador_selecionado = get_object_or_404(Doador, pk=request.POST.get('doador_id'))
        formulario = FormularioHistoricoDoacao(request.POST)
        if formulario.is_valid():
            HistoricoDoacao.objects.create(
                doador=doador_selecionado,
                data_doacao=formulario.cleaned_data['data_doacao'],
                local=formulario.cleaned_data['local'] or hemocentro.nome,
            )
            messages.success(request, f'Doação de {doador_selecionado.nome_completo} registrada com sucesso!')
            return redirect('hemocentros:painel')
        doadores_encontrados = []
        termo_busca = ''
        return render(request, 'hemocentros/registrar_doacao.html', {
            'formulario': formulario,
            'doador_selecionado': doador_selecionado,
            'termo_busca': termo_busca,
            'doadores_encontrados': doadores_encontrados,
        })

    termo_busca = request.GET.get('q', '').strip()
    doadores_encontrados = Doador.objects.filter(nome_completo__icontains=termo_busca)[:20] if termo_busca else []

    doador_selecionado = None
    formulario = None
    doador_id = request.GET.get('doador')
    if doador_id:
        doador_selecionado = get_object_or_404(Doador, pk=doador_id)
        formulario = FormularioHistoricoDoacao(initial={
            'data_doacao': timezone.now().date(),
            'local': hemocentro.nome,
        })

    return render(request, 'hemocentros/registrar_doacao.html', {
        'termo_busca': termo_busca,
        'doadores_encontrados': doadores_encontrados,
        'doador_selecionado': doador_selecionado,
        'formulario': formulario,
    })
