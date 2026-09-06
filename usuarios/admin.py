from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações adicionais', {'fields': ('tipo_usuario',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações adicionais', {'fields': ('tipo_usuario', 'email')}),
    )
