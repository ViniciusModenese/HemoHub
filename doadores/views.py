from datetime import date
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from hemocentros.models import Hemocentro
from hemoconecta.utilitarios import DOADORES_COMPATIVEIS, calcular_distancia_km
from usuarios.models import Usuario

from .forms import FormularioCadastroDoador, FormularioEditarDoador
from .models import Agendamento, Doador
from .servicos import criar_doador

CAMPOS_ENDERECO = ('logradouro', 'numero', 'bairro', 'cidade', 'estado')

HORARIOS_AGENDAMENTO = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00',
]


def cadastro(request):
    if request.method == 'POST':
        formulario = FormularioCadastroDoador(request.POST)
        if formulario.is_valid():
            dados = formulario.cleaned_data
            usuario = criar_doador(dados).usuario
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
    Agendamento.marcar_ausentes(doador=doador)
    agendamentos = doador.agendamentos.select_related('hemocentro').order_by('-data', '-horario')
    return render(request, 'doadores/painel.html', {
        'doador': doador,
        'apto': apto,
        'motivos': motivos,
        'proxima_data_apta': doador.proxima_data_apta(),
        'historico': doador.historico.all(),
        'agendamentos': agendamentos,
    })


@login_required
def escolher_hemocentro(request):
    if request.user.tipo_usuario != Usuario.TipoUsuario.DOADOR:
        messages.error(request, 'Apenas contas de doadores podem realizar agendamentos.')
        return redirect('paginas:inicio')

    doador = get_object_or_404(Doador, usuario=request.user)
    apto, motivos = doador.apto_para_doar()
    proxima_data = doador.proxima_data_apta()
    tem_localizacao = doador.latitude is not None and doador.longitude is not None

    hemocentros = Hemocentro.objects.filter(aprovado=True).prefetch_related('necessidades')
    opcoes = []
    for hemocentro in hemocentros:
        necessidades = [n for n in hemocentro.necessidades.all() if n.ativa]
        precisa_do_meu_tipo = any(
            doador.tipo_sanguineo in DOADORES_COMPATIVEIS[n.tipo_sanguineo] for n in necessidades
        )
        if any(n.nivel_urgencia == 'critica' for n in necessidades):
            status_demanda = 'urgente'
        elif any(n.nivel_urgencia == 'alta' for n in necessidades):
            status_demanda = 'alta'
        elif necessidades:
            status_demanda = 'normal'
        else:
            status_demanda = 'sem_demanda'

        distancia_km = None
        if tem_localizacao and hemocentro.latitude is not None and hemocentro.longitude is not None:
            distancia_km = calcular_distancia_km(
                float(doador.latitude), float(doador.longitude),
                float(hemocentro.latitude), float(hemocentro.longitude),
            )

        opcoes.append({
            'hemocentro': hemocentro,
            'status_demanda': status_demanda,
            'precisa_do_meu_tipo': precisa_do_meu_tipo,
            'distancia_km': distancia_km,
        })

    opcoes.sort(key=lambda o: (o['distancia_km'] is None, o['distancia_km'] or 0, o['hemocentro'].nome))

    return render(request, 'doadores/agendar.html', {
        'doador': doador,
        'apto': apto,
        'motivos': motivos,
        'proxima_data_apta': proxima_data,
        'data_minima': max(proxima_data, timezone.localdate()).isoformat(),
        'horarios': HORARIOS_AGENDAMENTO,
        'tem_localizacao': tem_localizacao,
        'agendamento_ativo': doador.agendamento_ativo(),
        'opcoes': opcoes,
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
            ativo = doador.agendamento_ativo()
            if ativo:
                resposta['agendamento_ativo'] = {
                    'hemocentro': ativo.hemocentro.nome,
                    'data': ativo.data.strftime('%d/%m/%Y'),
                    'horario': ativo.horario,
                }
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

    if horario not in HORARIOS_AGENDAMENTO:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Horário inválido. Escolha um dos horários oferecidos.'}, status=400)
        messages.error(request, 'Horário inválido. Escolha um dos horários oferecidos.')
        return redirect('doadores:escolher_hemocentro')

    try:
        data_agendada = date.fromisoformat(data_str)
    except ValueError:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Data inválida.'}, status=400)
        messages.error(request, 'Data inválida.')
        return redirect('paginas:inicio')

    if data_agendada < timezone.localdate():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': 'Não é possível agendar para datas passadas.'}, status=400)
        messages.error(request, 'Não é possível agendar para datas passadas.')
        return redirect('paginas:inicio')

    agora = timezone.localtime()
    erro = None
    if request.POST.get('aceite_requisitos') != 'on':
        erro = 'Para agendar, leia os requisitos para doação e confirme que atende a eles.'
    elif data_agendada == agora.date() and horario <= agora.strftime('%H:%M'):
        erro = 'Esse horário já passou. Escolha um horário futuro.'
    elif doador.agendamento_ativo():
        erro = 'Você já possui um agendamento confirmado. Cancele-o no painel antes de marcar outro.'
    if erro:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': erro}, status=400)
        messages.error(request, erro)
        return redirect('doadores:escolher_hemocentro')

    apto, motivos = doador.apto_para_doar()
    if not apto:
        proxima_data = doador.proxima_data_apta()
        if proxima_data <= timezone.localdate():
            erro = 'Você não está apta a doar no momento: ' + ' '.join(motivos)
        elif data_agendada < proxima_data:
            erro = (
                f'Você só poderá doar a partir de {proxima_data.strftime("%d/%m/%Y")}. '
                'Escolha uma data a partir desse dia.'
            )
        else:
            erro = None
        if erro:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
                return JsonResponse({'sucesso': False, 'erro': erro}, status=400)
            messages.error(request, erro)
            return redirect('doadores:escolher_hemocentro')

    try:
        with transaction.atomic():
            agendamento = Agendamento.objects.create(
                doador=doador,
                hemocentro=hemocentro,
                data=data_agendada,
                horario=horario,
                observacoes=observacoes,
                status=Agendamento.Status.CONFIRMADO,
            )
    except IntegrityError:
        erro = 'Você já possui um agendamento confirmado. Cancele-o no painel antes de marcar outro.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'sucesso': False, 'erro': erro}, status=400)
        messages.error(request, erro)
        return redirect('doadores:escolher_hemocentro')

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
    if agendamento.status != Agendamento.Status.CONFIRMADO:
        messages.error(request, 'Só é possível cancelar agendamentos confirmados. Este já foi concluído ou cancelado.')
        return redirect('doadores:painel')
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
