from datetime import date
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from hemocentros.models import Hemocentro
from usuarios.models import Usuario

from .forms import FormularioCadastroDoador, FormularioEditarDoador
from .models import Agendamento, Doador

CAMPOS_ENDERECO = ('logradouro', 'numero', 'bairro', 'cidade', 'estado')


def cadastro(request):
    if request.method == 'POST':
        formulario = FormularioCadastroDoador(request.POST)
        if formulario.is_valid():
            dados = formulario.cleaned_data
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
                    username=dados['username'],
                    email=dados['email'],
                    password=dados['password1'],
                    tipo_usuario=Usuario.TipoUsuario.DOADOR,
                )
                Doador.objects.create(
                    usuario=usuario,
                    nome_completo=dados['nome_completo'],
                    cpf=dados['cpf'],
                    data_nascimento=dados['data_nascimento'],
                    sexo=dados['sexo'],
                    peso=dados['peso'],
                    tipo_sanguineo=dados['tipo_sanguineo'],
                    telefone=dados['telefone'],
                    esta_gestante=dados['esta_gestante'],
                    data_ultimo_parto=dados['data_ultimo_parto'],
                    parto_cesarea=dados['parto_cesarea'],
                    logradouro=dados['logradouro'],
                    numero=dados['numero'],
                    bairro=dados['bairro'],
                    cidade=dados['cidade'],
                    estado=dados['estado'],
                    cep=dados['cep'],
                )
            login(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('doadores:painel')
    else:
        formulario = FormularioCadastroDoador()
    return render(request, 'doadores/cadastro.html', {'formulario': formulario})


@login_required
def painel(request):
    doador = get_object_or_404(Doador, usuario=request.user)
    apto, motivos = doador.apto_para_doar()
    agendamentos = doador.agendamentos.select_related('hemocentro').order_by('-data', '-horario')
    return render(request, 'doadores/painel.html', {
        'doador': doador,
        'apto': apto,
        'motivos': motivos,
        'proxima_data_apta': doador.proxima_data_apta(),
        'historico': doador.historico.all(),
        'agendamentos': agendamentos,
    })


def dados_agendamento_hemocentro(request, hemocentro_id):
    hemocentro = get_object_or_404(Hemocentro, pk=hemocentro_id)
    resposta = {
        'hemocentro': {
            'id': hemocentro.id,
            'nome': hemocentro.nome,
            'endereco': hemocentro.endereco_completo,
            'telefone': hemocentro.telefone or 'Não informado',
            'horario': hemocentro.horario_funcionamento or 'Segunda a Sexta das 08h às 17h',
        },
        'autenticado': request.user.is_authenticated,
        'tipo_usuario': request.user.tipo_usuario if request.user.is_authenticated else None,
        'doador': None,
    }

    if request.user.is_authenticated and request.user.tipo_usuario == Usuario.TipoUsuario.DOADOR:
        try:
            doador = request.user.doador
            apto, motivos = doador.apto_para_doar()
            proxima_data = doador.proxima_data_apta()
            resposta['doador'] = {
                'id': doador.id,
                'nome': doador.nome_completo,
                'tipo_sanguineo': doador.tipo_sanguineo,
                'apto': apto,
                'motivos': motivos,
                'proxima_data_apta': proxima_data.strftime('%Y-%m-%d') if proxima_data else None,
                'proxima_data_apta_formatada': proxima_data.strftime('%d/%m/%Y') if proxima_data else None,
            }
        except Doador.DoesNotExist:
            pass

    return JsonResponse(resposta)


@login_required
@require_POST
def criar_agendamento(request, hemocentro_id):
    if request.user.tipo_usuario != Usuario.TipoUsuario.DOADOR:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Apenas contas de doadores podem realizar agendamentos.'}, status=403)
        messages.error(request, 'Apenas contas de doadores podem realizar agendamentos.')
        return redirect('paginas:inicio')

    doador = get_object_or_404(Doador, usuario=request.user)
    hemocentro = get_object_or_404(Hemocentro, pk=hemocentro_id)

    data_str = request.POST.get('data')
    horario = request.POST.get('horario')
    observacoes = request.POST.get('observacoes', '').strip()

    if not data_str or not horario:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Data e horário são obrigatórios.'}, status=400)
        messages.error(request, 'Por favor, selecione data e horário para a doação.')
        return redirect('paginas:inicio')

    try:
        data_agendada = date.fromisoformat(data_str)
    except ValueError:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Data inválida.'}, status=400)
        messages.error(request, 'Data inválida.')
        return redirect('paginas:inicio')

    if data_agendada < date.today():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Não é possível agendar para datas passadas.'}, status=400)
        messages.error(request, 'Não é possível agendar para datas passadas.')
        return redirect('paginas:inicio')

    agendamento = Agendamento.objects.create(
        doador=doador,
        hemocentro=hemocentro,
        data=data_agendada,
        horario=horario,
        observacoes=observacoes,
        status=Agendamento.Status.CONFIRMADO,
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({
            'sucesso': True,
            'agendamento_id': agendamento.id,
            'data': agendamento.data.strftime('%d/%m/%Y'),
            'horario': agendamento.horario,
            'hemocentro_nome': hemocentro.nome,
            'mensagem': f'Agendamento confirmado para {agendamento.data.strftime("%d/%m/%Y")} às {agendamento.horario}!'
        })

    messages.success(request, f'Doação agendada com sucesso em {hemocentro.nome} para {agendamento.data.strftime("%d/%m/%Y")} às {agendamento.horario}!')
    return redirect('doadores:painel')


@login_required
@require_POST
def cancelar_agendamento(request, agendamento_id):
    doador = get_object_or_404(Doador, usuario=request.user)
    agendamento = get_object_or_404(Agendamento, pk=agendamento_id, doador=doador)
    agendamento.status = Agendamento.Status.CANCELADO
    agendamento.save()
    messages.success(request, 'Agendamento cancelado com sucesso.')
    return redirect('doadores:painel')


@login_required
def editar(request):
    doador = get_object_or_404(Doador, usuario=request.user)
    if request.method == 'POST':
        formulario = FormularioEditarDoador(request.POST, instance=doador)
        if formulario.is_valid():
            endereco_antigo = tuple(getattr(doador, campo) for campo in CAMPOS_ENDERECO)
            doador_atualizado = formulario.save(commit=False)
            endereco_novo = tuple(getattr(doador_atualizado, campo) for campo in CAMPOS_ENDERECO)
            if endereco_novo != endereco_antigo:
                doador_atualizado.latitude = None
                doador_atualizado.longitude = None
            doador_atualizado.save()
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('doadores:painel')
    else:
        formulario = FormularioEditarDoador(instance=doador)
    return render(request, 'doadores/editar.html', {'formulario': formulario, 'doador': doador})
