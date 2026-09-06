from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class TipoUsuario(models.TextChoices):
        HEMOCENTRO = 'hemocentro', 'Hemocentro'
        DOADOR = 'doador', 'Doador'

    tipo_usuario = models.CharField(max_length=20, choices=TipoUsuario.choices)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.get_full_name() or self.username
