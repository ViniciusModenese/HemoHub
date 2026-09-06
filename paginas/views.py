from django.http import JsonResponse
from django.shortcuts import render

from doadores.models import Doador, HistoricoDoacao
from hemocentros.models import Hemocentro
from hemoconecta.utilitarios import DOADORES_COMPATIVEIS
from necessidades.models import NecessidadeSanguinea


PODE_DOAR_PARA = {}
for receptor, doadores in DOADORES_COMPATIVEIS.items():
    for doador in doadores:
        PODE_DOAR_PARA.setdefault(doador, []).append(receptor)


DESCRICOES_TIPOS = {
    'A+': 'Tipo A positivo. É um dos tipos mais comuns na população brasileira.',
    'A-': 'Tipo A negativo. Relativamente raro, muito valioso para transfusões.',
    'B+': 'Tipo B positivo. Encontrado em cerca de 8% da população.',
    'B-': 'Tipo B negativo. Um dos tipos mais raros, cada doação faz grande diferença.',
    'AB+': 'Tipo AB positivo. Receptor universal — pode receber de todos os tipos.',
    'AB-': 'Tipo AB negativo. O tipo mais raro. Pode receber de todos os tipos negativos.',
    'O+': 'Tipo O positivo. O tipo mais comum no Brasil, com alta demanda constante.',
    'O-': 'Tipo O negativo. Doador universal — pode doar para qualquer pessoa.',
}


def inicio(request):
    tipos_sanguineos_info = []
    for tipo in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']:
        tipos_sanguineos_info.append({
            'tipo': tipo,
            'descricao': DESCRICOES_TIPOS.get(tipo, ''),
            'pode_doar_para': sorted(PODE_DOAR_PARA.get(tipo, [])),
            'pode_receber_de': sorted(DOADORES_COMPATIVEIS.get(tipo, [])),
        })

    contexto = {
        'total_hemocentros': Hemocentro.objects.filter(aprovado=True).count(),
        'total_doadores': Doador.objects.count(),
        'total_necessidades_ativas': NecessidadeSanguinea.objects.filter(ativa=True).count(),
        'total_doacoes': HistoricoDoacao.objects.count(),
        'tipos_sanguineos_info': tipos_sanguineos_info,
    }
    return render(request, 'paginas/inicio.html', contexto)


def dados_mapa(request):
    hemocentros = Hemocentro.objects.filter(
        aprovado=True, latitude__isnull=False, longitude__isnull=False
    ).prefetch_related('fotos', 'necessidades')

    dados = []
    for hemocentro in hemocentros:
        necessidades_ativas = list(hemocentro.necessidades.filter(ativa=True))
        
        if not necessidades_ativas:
            status_demanda = 'sem_demanda'
        elif any(n.nivel_urgencia == 'critica' for n in necessidades_ativas):
            status_demanda = 'urgente'
        elif any(n.nivel_urgencia == 'alta' for n in necessidades_ativas):
            status_demanda = 'alta'
        else:
            status_demanda = 'normal'

        tem_urgencia = status_demanda in ['alta', 'urgente']

        dados.append({
            'id': hemocentro.id,
            'nome': hemocentro.nome,
            'descricao': hemocentro.descricao,
            'telefone': hemocentro.telefone,
            'endereco': hemocentro.endereco_completo,
            'horario_funcionamento': hemocentro.horario_funcionamento,
            'latitude': float(hemocentro.latitude),
            'longitude': float(hemocentro.longitude),
            'tem_urgencia': tem_urgencia,
            'status_demanda': status_demanda,
            'fotos': [foto.imagem.url for foto in hemocentro.fotos.all()],
            'necessidades': [
                {
                    'tipo_sanguineo': necessidade.tipo_sanguineo,
                    'nivel_urgencia': necessidade.get_nivel_urgencia_display(),
                    'nivel_urgencia_raw': necessidade.nivel_urgencia,
                    'quantidade_bolsas': necessidade.quantidade_bolsas,
                }
                for necessidade in necessidades_ativas
            ],
        })

    return JsonResponse({'hemocentros': dados})
