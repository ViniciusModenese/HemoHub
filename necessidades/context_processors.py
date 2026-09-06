from usuarios.models import Usuario


def notificacoes_doador(request):
    usuario = getattr(request, 'user', None)
    if not usuario or not usuario.is_authenticated or usuario.tipo_usuario != Usuario.TipoUsuario.DOADOR:
        return {}

    doador = getattr(usuario, 'doador', None)
    if doador is None:
        return {}

    notificacoes = doador.notificacoes.select_related('necessidade__hemocentro').all()[:8]
    return {
        'notificacoes_usuario': notificacoes,
        'notificacoes_nao_lidas': doador.notificacoes.filter(lida=False).count(),
    }
