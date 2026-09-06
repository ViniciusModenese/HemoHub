from django.contrib import admin

from .models import NecessidadeSanguinea, NotificacaoDoador


@admin.register(NecessidadeSanguinea)
class NecessidadeSanguineaAdmin(admin.ModelAdmin):
    list_display = ('hemocentro', 'tipo_sanguineo', 'nivel_urgencia', 'ativa', 'notificacao_enviada')
    list_filter = ('nivel_urgencia', 'ativa', 'tipo_sanguineo')


@admin.register(NotificacaoDoador)
class NotificacaoDoadorAdmin(admin.ModelAdmin):
    list_display = ('doador', 'necessidade', 'lida', 'criado_em')
    list_filter = ('lida',)
