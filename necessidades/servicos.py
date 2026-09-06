from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from doadores.models import Doador
from hemoconecta.utilitarios import DOADORES_COMPATIVEIS, calcular_distancia_km

from .models import NotificacaoDoador


def buscar_doadores_compativeis_proximos(necessidade):
    hemocentro = necessidade.hemocentro
    if hemocentro.latitude is None or hemocentro.longitude is None:
        return []

    tipos_compativeis = DOADORES_COMPATIVEIS.get(necessidade.tipo_sanguineo, [])
    raio_km = settings.RAIO_NOTIFICACAO_URGENCIA_KM

    candidatos = Doador.objects.filter(
        tipo_sanguineo__in=tipos_compativeis,
        latitude__isnull=False,
        longitude__isnull=False,
    )

    doadores_proximos = []
    for doador in candidatos:
        distancia_km = calcular_distancia_km(
            float(hemocentro.latitude), float(hemocentro.longitude),
            float(doador.latitude), float(doador.longitude),
        )
        if distancia_km <= raio_km:
            doadores_proximos.append(doador)

    return doadores_proximos


def notificar_doadores_proximos(necessidade):
    doadores = buscar_doadores_compativeis_proximos(necessidade)

    assunto = f'Urgência de sangue tipo {necessidade.tipo_sanguineo} - {necessidade.hemocentro.nome}'

    for doador in doadores:
        mensagem = render_to_string('necessidades/email_urgencia.txt', {
            'doador': doador,
            'necessidade': necessidade,
        })
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [doador.usuario.email],
            fail_silently=True,
        )
        NotificacaoDoador.objects.create(doador=doador, necessidade=necessidade)

    return len(doadores)
