from datetime import date, timedelta
from urllib.parse import parse_qsl, urlencode

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Case, CharField, DateField, F, IntegerField, Max, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from doadores.forms import FormularioCadastroDoador, FormularioHistoricoDoacao
from doadores.models import INTERVALO_DIAS_DOACAO, Agendamento, Doador, HistoricoDoacao
from doadores.servicos import criar_doador
from hemoconecta.utilitarios import TIPOS_SANGUINEOS, normalizar_cpf
from necessidades.models import NecessidadeSanguinea
from necessidades.servicos import buscar_doadores_compativeis_proximos
from usuarios.models import Usuario

from .forms import (
    FormularioCadastroHemocentro, FormularioEditarHemocentro, FormularioEstoque, nome_do_campo_estoque,
)
from .models import EstoqueSanguineo, FotoHemocentro, Hemocentro, nivel_do_estoque

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


def _ler_data(valor):
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def _ultimos_alertas(hemocentro):
    return dict(
        NecessidadeSanguinea.objects.filter(hemocentro=hemocentro, notificacao_enviada=True)
        .values_list('tipo_sanguineo')
        .annotate(ultimo=Max('criado_em'))
    )


def _resumo_do_estoque(hemocentro):
    registros = {e.tipo_sanguineo: e for e in hemocentro.estoque.all()}
    ultimos_alertas = _ultimos_alertas(hemocentro)
    resumo = []
    for tipo, _ in TIPOS_SANGUINEOS:
        registro = registros.get(tipo)
        quantidade = registro.quantidade_bolsas if registro else 0
        resumo.append({
            'tipo': tipo,
            'quantidade': quantidade,
            'nivel': nivel_do_estoque(quantidade),
            'percentual': registro.percentual if registro else 0,
            'atualizado_em': registro.atualizado_em if registro else None,
            'ultimo_alerta': ultimos_alertas.get(tipo),
        })
    return resumo


@login_required
def emitir_alerta_estoque(request):
    if request.method != 'POST':
        return redirect('hemocentros:painel')
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    tipo = request.POST.get('tipo')
    if tipo not in dict(TIPOS_SANGUINEOS):
        messages.error(request, 'Tipo sanguíneo inválido.')
        return redirect('hemocentros:painel')

    registro = hemocentro.estoque.filter(tipo_sanguineo=tipo).first()
    quantidade = registro.quantidade_bolsas if registro else 0
    if nivel_do_estoque(quantidade) != 'critico':
        messages.error(request, f'O estoque de {tipo} não está em nível crítico, por isso não é possível emitir alerta.')
        return redirect('hemocentros:painel')

    necessidade = NecessidadeSanguinea(
        hemocentro=hemocentro,
        tipo_sanguineo=tipo,
        nivel_urgencia=NecessidadeSanguinea.NivelUrgencia.CRITICA,
        observacoes=f'Alerta emitido pelo painel de estoque ({quantidade} bolsa{"s" if quantidade != 1 else ""} em estoque).',
    )
    notificados = len(buscar_doadores_compativeis_proximos(necessidade))
    with transaction.atomic():
        hemocentro.necessidades.filter(tipo_sanguineo=tipo, ativa=True).update(ativa=False)
        necessidade.save()
    if notificados:
        messages.success(request, f'Alerta de {tipo} emitido. {notificados} doador(es) compatível(is) em até {settings.RAIO_NOTIFICACAO_URGENCIA_KM} km notificado(s).')
    else:
        messages.warning(request, f'Alerta de {tipo} emitido, mas não há doadores compatíveis em até {settings.RAIO_NOTIFICACAO_URGENCIA_KM} km.')
    return redirect('hemocentros:painel')


@login_required
def atualizar_estoque(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    if request.method == 'POST':
        formulario = FormularioEstoque(request.POST)
        if formulario.is_valid():
            existentes = {e.tipo_sanguineo: e for e in hemocentro.estoque.all()}
            agora = timezone.now()
            novos, alterados = [], []
            for tipo, _ in TIPOS_SANGUINEOS:
                quantidade = formulario.cleaned_data[nome_do_campo_estoque(tipo)]
                registro = existentes.get(tipo)
                if registro is None:
                    novos.append(EstoqueSanguineo(hemocentro=hemocentro, tipo_sanguineo=tipo, quantidade_bolsas=quantidade))
                elif registro.quantidade_bolsas != quantidade:
                    registro.quantidade_bolsas = quantidade
                    registro.atualizado_em = agora
                    alterados.append(registro)
            with transaction.atomic():
                EstoqueSanguineo.objects.bulk_create(novos)
                EstoqueSanguineo.objects.bulk_update(alterados, ['quantidade_bolsas', 'atualizado_em'])
            messages.success(request, 'Estoque atualizado com sucesso!')
            return redirect('hemocentros:painel')
    else:
        atuais = {e.tipo_sanguineo: e.quantidade_bolsas for e in hemocentro.estoque.all()}
        formulario = FormularioEstoque(initial={
            nome_do_campo_estoque(tipo): atuais.get(tipo, 0) for tipo, _ in TIPOS_SANGUINEOS
        })
    return render(request, 'hemocentros/estoque.html', {'hemocentro': hemocentro, 'formulario': formulario})


@login_required
def painel(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    necessidades = hemocentro.necessidades.all()
    Agendamento.marcar_ausentes(hemocentro=hemocentro)
    confirmado = Agendamento.Status.CONFIRMADO
    todos = hemocentro.agendamentos.select_related('doador').annotate(
        grupo=Case(
            When(status=confirmado, then=0),
            When(status=Agendamento.Status.CONCLUIDO, then=1),
            default=2,
            output_field=IntegerField(),
        ),
        pendente_data=Case(When(status=confirmado, then=F('data')), output_field=DateField()),
        pendente_horario=Case(When(status=confirmado, then=F('horario')), output_field=CharField()),
        encerrado_data=Case(When(~Q(status=confirmado), then=F('data')), output_field=DateField()),
        encerrado_horario=Case(When(~Q(status=confirmado), then=F('horario')), output_field=CharField()),
    ).order_by('grupo', 'pendente_data', 'pendente_horario', F('encerrado_data').desc(), F('encerrado_horario').desc())

    status = request.GET.get('status', '')
    data_inicial = _ler_data(request.GET.get('de'))
    data_final = _ler_data(request.GET.get('ate'))
    if status in Agendamento.Status.values:
        todos = todos.filter(status=status)
    else:
        status = ''
    if data_inicial:
        todos = todos.filter(data__gte=data_inicial)
    if data_final:
        todos = todos.filter(data__lte=data_final)

    pagina = Paginator(todos, 20).get_page(request.GET.get('pagina'))
    consulta_filtros = urlencode([(k, v) for k, v in request.GET.items() if k in ('status', 'de', 'ate') and v])
    return render(request, 'hemocentros/painel.html', {
        'hemocentro': hemocentro,
        'necessidades': necessidades,
        'agendamentos': pagina,
        'consulta_filtros': consulta_filtros,
        'hoje': timezone.localdate(),
        'filtros': {
            'status': status,
            'de': data_inicial.isoformat() if data_inicial else '',
            'ate': data_final.isoformat() if data_final else '',
        },
        'filtrado': bool(status or data_inicial or data_final),
        'consulta_atual': request.GET.urlencode(),
        'estoque': _resumo_do_estoque(hemocentro),
        'raio_km': settings.RAIO_NOTIFICACAO_URGENCIA_KM,
        'opcoes_status': Agendamento.Status.choices,
    })


def _aviso_do_estoque(doador):
    return f' Estoque de {doador.tipo_sanguineo}: +1 bolsa.'


def _voltar_ao_painel(request):
    permitidos = [(chave, valor) for chave, valor in parse_qsl(request.POST.get('voltar', '')) if chave in ('status', 'de', 'ate', 'pagina')]
    url = reverse('hemocentros:painel')
    return redirect(f'{url}?{urlencode(permitidos)}' if permitidos else url)


@login_required
def atualizar_agendamento(request, agendamento_id):
    if request.method != 'POST':
        return redirect('hemocentros:painel')
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    agendamento = get_object_or_404(Agendamento, pk=agendamento_id, hemocentro=hemocentro)
    Agendamento.marcar_ausentes(hemocentro=hemocentro)
    agendamento.refresh_from_db()
    acao = request.POST.get('acao')
    if agendamento.status != Agendamento.Status.CONFIRMADO:
        messages.error(request, 'Este agendamento já foi concluído, cancelado ou marcado como ausente.')
        return _voltar_ao_painel(request)
    if acao == 'concluir':
        if agendamento.data > timezone.localdate():
            messages.error(
                request,
                f'A doação de {agendamento.doador.nome_completo} está agendada para '
                f'{agendamento.data.strftime("%d/%m/%Y")} e só pode ser concluída a partir dessa data.',
            )
            return _voltar_ao_painel(request)
        erro = _erro_na_data_da_doacao(agendamento.doador, agendamento.data)
        restricoes = _restricoes_do_doador(agendamento.doador)
        if restricoes:
            erro = erro or 'O doador não está apto a doar: ' + ' '.join(restricoes)
        if erro:
            messages.error(request, erro)
            return _voltar_ao_painel(request)
        with transaction.atomic():
            agendamento.status = Agendamento.Status.CONCLUIDO
            agendamento.save()
            HistoricoDoacao.objects.create(
                doador=agendamento.doador,
                data_doacao=agendamento.data,
                local=hemocentro.nome,
            )
            hemocentro.registrar_entrada_no_estoque(agendamento.doador.tipo_sanguineo)
            cancelados = _cancelar_agendamentos_em_conflito(agendamento.doador, agendamento.data, mantido=agendamento)
        messages.success(request, f'Doação de {agendamento.doador.nome_completo} confirmada e registrada com sucesso!' + _aviso_do_estoque(agendamento.doador))
        _avisar_cancelados(request, cancelados)
    elif acao == 'cancelar':
        agendamento.status = Agendamento.Status.CANCELADO
        agendamento.save()
        messages.info(request, f'Agendamento de {agendamento.doador.nome_completo} cancelado.')
    return _voltar_ao_painel(request)


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


def _cancelar_agendamentos_em_conflito(doador, data_doacao, mantido=None):
    limite = data_doacao + timedelta(days=INTERVALO_DIAS_DOACAO[doador.sexo])
    conflitantes = doador.agendamentos.filter(status=Agendamento.Status.CONFIRMADO, data__lt=limite)
    if mantido is not None:
        conflitantes = conflitantes.exclude(pk=mantido.pk)
    cancelados = list(conflitantes.select_related('hemocentro'))
    for agendamento in cancelados:
        agendamento.status = Agendamento.Status.CANCELADO
        agendamento.save()
    return cancelados


def _avisar_cancelados(request, cancelados):
    for agendamento in cancelados:
        messages.info(
            request,
            f'O agendamento de {agendamento.data.strftime("%d/%m/%Y")} em {agendamento.hemocentro.nome} '
            'foi cancelado, pois ficaria dentro do intervalo mínimo entre doações.',
        )


def _atualizar_agendamentos_apos_doacao(doador, hemocentro, data_doacao):
    limite = data_doacao + timedelta(days=INTERVALO_DIAS_DOACAO[doador.sexo])
    cumprido = (
        doador.agendamentos.filter(status=Agendamento.Status.CONFIRMADO, hemocentro=hemocentro, data__lt=limite)
        .order_by('data', 'horario')
        .first()
    )
    if cumprido:
        cumprido.status = Agendamento.Status.CONCLUIDO
        cumprido.data = data_doacao
        cumprido.save()
    else:
        Agendamento.objects.create(
            doador=doador,
            hemocentro=hemocentro,
            data=data_doacao,
            horario=timezone.localtime().strftime('%H:%M'),
            status=Agendamento.Status.CONCLUIDO,
            observacoes='Doação registrada diretamente pelo hemocentro.',
        )
    return _cancelar_agendamentos_em_conflito(doador, data_doacao, mantido=cumprido)


def _formulario_doador_presencial(dados=None):
    formulario = FormularioCadastroDoador(dados)
    formulario.fields['username'].widget.attrs['autocomplete'] = 'off'
    formulario.fields['email'].widget.attrs['autocomplete'] = 'off'
    formulario.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
    formulario.fields['password2'].widget.attrs['autocomplete'] = 'new-password'
    return formulario


MINIMO_LETRAS_NA_BUSCA = 3


def _buscar_doadores_na_rede(termo):
    cpf = normalizar_cpf(termo)
    if cpf:
        return Doador.objects.filter(cpf__in=[cpf, ''.join(c for c in cpf if c.isdigit())])[:20]
    if len(termo) >= MINIMO_LETRAS_NA_BUSCA:
        return Doador.objects.filter(nome_completo__icontains=termo)[:20]
    return []


def _restricoes_do_doador(doador):
    apto, motivos = doador.apto_para_doar(considerar_idade=False)
    return [] if apto else motivos


def _erro_na_data_da_doacao(doador, data_doacao):
    if data_doacao > timezone.localdate():
        return 'A data da doação não pode ser futura.'
    ultima = doador.data_ultima_doacao()
    intervalo = INTERVALO_DIAS_DOACAO[doador.sexo]
    if ultima and abs((data_doacao - ultima).days) < intervalo:
        return (
            f'Este doador já tem doação registrada em {ultima.strftime("%d/%m/%Y")}. '
            f'O intervalo mínimo entre doações é de {intervalo} dias.'
        )
    return None


@login_required
def registrar_doacao(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)

    if request.method == 'POST':
        doador_selecionado = get_object_or_404(Doador, pk=request.POST.get('doador_id'))
        formulario = FormularioHistoricoDoacao(request.POST)
        if formulario.is_valid():
            data_doacao = formulario.cleaned_data['data_doacao']
            erro = _erro_na_data_da_doacao(doador_selecionado, data_doacao)
            restricoes = _restricoes_do_doador(doador_selecionado)
            if restricoes:
                formulario.add_error(None, 'O doador não está apto a doar: ' + ' '.join(restricoes))
            elif erro:
                formulario.add_error('data_doacao', erro)
            else:
                with transaction.atomic():
                    HistoricoDoacao.objects.create(
                        doador=doador_selecionado,
                        data_doacao=data_doacao,
                        local=formulario.cleaned_data['local'] or hemocentro.nome,
                    )
                    cancelados = _atualizar_agendamentos_apos_doacao(doador_selecionado, hemocentro, data_doacao)
                    hemocentro.registrar_entrada_no_estoque(doador_selecionado.tipo_sanguineo)
                messages.success(request, f'Doação de {doador_selecionado.nome_completo} registrada com sucesso!' + _aviso_do_estoque(doador_selecionado))
                _avisar_cancelados(request, cancelados)
                return redirect('hemocentros:painel')
        return render(request, 'hemocentros/registrar_doacao.html', {
            'formulario': formulario,
            'doador_selecionado': doador_selecionado,
            'restricoes': _restricoes_do_doador(doador_selecionado),
            'termo_busca': '',
            'doadores_encontrados': [],
            'formulario_doador': _formulario_doador_presencial(),
        })

    termo_busca = request.GET.get('q', '').strip()
    doadores_encontrados = _buscar_doadores_na_rede(termo_busca) if termo_busca else []

    doador_selecionado = None
    formulario = None
    doador_id = request.GET.get('doador')
    if doador_id:
        doador_selecionado = get_object_or_404(Doador, pk=doador_id)
        formulario = FormularioHistoricoDoacao(initial={
            'data_doacao': timezone.localdate(),
            'local': hemocentro.nome,
        })

    return render(request, 'hemocentros/registrar_doacao.html', {
        'termo_busca': termo_busca,
        'doadores_encontrados': doadores_encontrados,
        'doador_selecionado': doador_selecionado,
        'restricoes': _restricoes_do_doador(doador_selecionado) if doador_selecionado else [],
        'formulario': formulario,
        'formulario_doador': _formulario_doador_presencial(),
    })


@login_required
def cadastrar_doador_presencial(request):
    hemocentro = get_object_or_404(Hemocentro, usuario=request.user)
    if request.method != 'POST':
        return redirect('hemocentros:registrar_doacao')
    formulario = _formulario_doador_presencial(request.POST)
    if formulario.is_valid():
        with transaction.atomic():
            doador = criar_doador(formulario.cleaned_data)
            Agendamento.objects.create(
                doador=doador,
                hemocentro=hemocentro,
                data=timezone.localdate(),
                horario=timezone.localtime().strftime('%H:%M'),
                observacoes='Atendimento presencial: cadastro feito no hemocentro.',
                status=Agendamento.Status.CONFIRMADO,
            )
        messages.success(request, f'Doador {doador.nome_completo} cadastrado. Confira os dados e confirme a doação.')
        return redirect(f"{reverse('hemocentros:registrar_doacao')}?doador={doador.pk}")
    return render(request, 'hemocentros/registrar_doacao.html', {
        'termo_busca': '',
        'doadores_encontrados': [],
        'doador_selecionado': None,
        'formulario': None,
        'formulario_doador': formulario,
        'abrir_modal_cadastro': True,
    })
