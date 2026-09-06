from django.db import models

from doadores.models import Doador
from hemoconecta.utilitarios import TIPOS_SANGUINEOS
from hemocentros.models import Hemocentro


class NecessidadeSanguinea(models.Model):

    class NivelUrgencia(models.TextChoices):
        BAIXA = 'baixa', 'Baixa'
        MEDIA = 'media', 'Média'
        ALTA = 'alta', 'Alta'
        CRITICA = 'critica', 'Crítica'

    hemocentro = models.ForeignKey(Hemocentro, on_delete=models.CASCADE, related_name='necessidades')
    tipo_sanguineo = models.CharField(max_length=3, choices=TIPOS_SANGUINEOS)
    nivel_urgencia = models.CharField(max_length=10, choices=NivelUrgencia.choices, default=NivelUrgencia.MEDIA)
    quantidade_bolsas = models.PositiveIntegerField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    notificacao_enviada = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    NIVEIS_QUE_NOTIFICAM = (NivelUrgencia.ALTA, NivelUrgencia.CRITICA)

    class Meta:
        verbose_name = 'Necessidade de sangue'
        verbose_name_plural = 'Necessidades de sangue'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.hemocentro.nome} - {self.tipo_sanguineo} ({self.get_nivel_urgencia_display()})'

    @property
    def deve_notificar(self):
        return self.ativa and not self.notificacao_enviada and self.nivel_urgencia in self.NIVEIS_QUE_NOTIFICAM


class NotificacaoDoador(models.Model):
    doador = models.ForeignKey(Doador, on_delete=models.CASCADE, related_name='notificacoes')
    necessidade = models.ForeignKey(NecessidadeSanguinea, on_delete=models.CASCADE, related_name='notificacoes_doadores')
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação de doador'
        verbose_name_plural = 'Notificações de doadores'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.doador.nome_completo} - {self.necessidade}'
