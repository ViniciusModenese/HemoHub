from django.contrib import admin

from .models import FotoHemocentro, Hemocentro


class FotoHemocentroInline(admin.TabularInline):
    model = FotoHemocentro
    extra = 1


@admin.register(Hemocentro)
class HemocentroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'aprovado')
    list_filter = ('estado', 'aprovado')
    search_fields = ('nome', 'cidade')
    inlines = [FotoHemocentroInline]
