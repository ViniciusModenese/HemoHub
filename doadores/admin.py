from django.contrib import admin

from .models import Doador, HistoricoDoacao


class HistoricoDoacaoInline(admin.TabularInline):
    model = HistoricoDoacao
    extra = 1


@admin.register(Doador)
class DoadorAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'tipo_sanguineo', 'cidade', 'estado')
    list_filter = ('tipo_sanguineo', 'estado')
    search_fields = ('nome_completo', 'cpf')
    inlines = [HistoricoDoacaoInline]
