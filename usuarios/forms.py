from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django import forms
from .models import Usuario


class FormularioLogin(AuthenticationForm):
    tipo_perfil = forms.CharField(
        required=False,
        initial='doador',
        widget=forms.HiddenInput()
    )
    username = forms.CharField(
        label='E-mail',
        widget=forms.TextInput(attrs={
            'class': 'form-control input-login-custom',
            'placeholder': 'joao@email.com',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input-login-custom',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        tipo_perfil = self.cleaned_data.get('tipo_perfil') or 'doador'

        if username and password:
            username = username.strip()
            self.cleaned_data['username'] = username
            if '@' in username:
                user_obj = Usuario.objects.filter(email__iexact=username).first()
                if user_obj:
                    username = user_obj.username
                    self.cleaned_data['username'] = username

            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

                if self.user_cache.tipo_usuario and self.user_cache.tipo_usuario != tipo_perfil:
                    if self.user_cache.tipo_usuario == Usuario.TipoUsuario.HEMOCENTRO:
                        raise forms.ValidationError(
                            'Esta conta pertence a um Hemocentro. Selecione a opção "Sou Hemocentro" acima para entrar.'
                        )
                    elif self.user_cache.tipo_usuario == Usuario.TipoUsuario.DOADOR:
                        raise forms.ValidationError(
                            'Esta conta pertence a um Doador. Selecione a opção "Sou Doador" acima para entrar.'
                        )

        return self.cleaned_data
