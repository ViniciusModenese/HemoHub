from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect

from .forms import FormularioLogin
from .models import Usuario


class TelaLogin(LoginView):
    template_name = 'usuarios/login.html'
    form_class = FormularioLogin
    redirect_authenticated_user = True


class TelaLogout(LogoutView):
    pass


@login_required
def redirecionar_painel(request):
    if request.user.tipo_usuario == Usuario.TipoUsuario.HEMOCENTRO:
        return redirect('hemocentros:painel')
    return redirect('doadores:painel')
