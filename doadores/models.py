from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from hemoconecta.utilitarios import TIPOS_SANGUINEOS, obter_coordenadas_endereco
from hemocentros.models import ESTADOS_BRASIL, Hemocentro

INTERVALO_DIAS_DOACAO = {'M': 60, 'F': 90}
LIMITE_DOACOES_ANO = {'M': 4, 'F': 3}
IDADE_MINIMA = 16
IDADE_MAXIMA = 69
IDADE_LIMITE_PRIMEIRA_DOACAO = 60
PESO_MINIMO_KG = 50
DIAS_POS_PARTO_NORMAL = 90
DIAS_POS_PARTO_CESAREA = 180


class Doador(models.Model):

    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMININO = 'F', 'Feminino'

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doador')
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    peso = models.DecimalField(max_digits=5, decimal_places=1, help_text='Peso em kg')
    tipo_sanguineo = models.CharField(max_length=3, choices=TIPOS_SANGUINEOS)
    telefone = models.CharField(max_length=20, blank=True)

    esta_gestante = models.BooleanField(default=False)
    data_ultimo_parto = models.DateField(null=True, blank=True)
    parto_cesarea = models.BooleanField(default=False)

    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2, choices=ESTADOS_BRASIL)
    cep = models.CharField(max_length=9)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doador'
        verbose_name_plural = 'Doadores'
        ordering = ['nome_completo']

    def __str__(self):
        return self.nome_completo

    @property
    def endereco_completo(self):
        return f'{self.logradouro}, {self.numero} - {self.bairro}, {self.cidade} - {self.estado}, {self.cep}'

    @property
    def idade(self):
        hoje = timezone.now().date()
        nascimento = self.data_nascimento
        return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))

    def geocodificar(self):
        latitude, longitude = obter_coordenadas_endereco(
            self.logradouro, self.numero, self.bairro, self.cidade, self.estado
        )
        self.latitude = latitude
        self.longitude = longitude

    def save(self, *args, **kwargs):
        if self.latitude is None or self.longitude is None:
            self.geocodificar()
        super().save(*args, **kwargs)

    def data_ultima_doacao(self):
        ultima = self.historico.order_by('-data_doacao').first()
        return ultima.data_doacao if ultima else None

    def doacoes_ultimos_12_meses(self):
        limite = timezone.now().date() - timedelta(days=365)
        return self.historico.filter(data_doacao__gte=limite).count()

    def apto_para_doar(self):
        motivos = []
        idade = self.idade
        ultima_doacao = self.data_ultima_doacao()

        if idade < IDADE_MINIMA:
            motivos.append(f'Idade mínima para doação é {IDADE_MINIMA} anos.')
        elif idade > IDADE_MAXIMA:
            motivos.append(f'Idade máxima para doação é {IDADE_MAXIMA} anos.')
        elif idade >= IDADE_LIMITE_PRIMEIRA_DOACAO and ultima_doacao is None:
            motivos.append(
                f'Após os {IDADE_LIMITE_PRIMEIRA_DOACAO} anos, só pode doar quem já doou antes dessa idade.'
            )

        if self.peso < PESO_MINIMO_KG:
            motivos.append(f'Peso mínimo para doação é {PESO_MINIMO_KG} kg.')

        if self.esta_gestante:
            motivos.append('Gestantes não podem doar sangue.')

        if self.data_ultimo_parto:
            limite_dias = DIAS_POS_PARTO_CESAREA if self.parto_cesarea else DIAS_POS_PARTO_NORMAL
            dias_desde_parto = (timezone.now().date() - self.data_ultimo_parto).days
            if dias_desde_parto < limite_dias:
                motivos.append(
                    f'Após o parto é necessário aguardar {limite_dias} dias '
                    f'(faltam {limite_dias - dias_desde_parto} dias).'
                )

        intervalo_dias = INTERVALO_DIAS_DOACAO[self.sexo]
        limite_anual = LIMITE_DOACOES_ANO[self.sexo]

        if ultima_doacao:
            dias_desde_ultima = (timezone.now().date() - ultima_doacao).days
            if dias_desde_ultima < intervalo_dias:
                motivos.append(
                    f'Intervalo mínimo entre doações é de {intervalo_dias} dias '
                    f'(faltam {intervalo_dias - dias_desde_ultima} dias).'
                )

        if self.doacoes_ultimos_12_meses() >= limite_anual:
            motivos.append(f'Limite de {limite_anual} doações nos últimos 12 meses já atingido.')

        return (len(motivos) == 0, motivos)

    def proxima_data_apta(self):
        apto, motivos = self.apto_para_doar()
        hoje = timezone.now().date()
        if apto:
            return hoje

        candidatas = [hoje]
        ultima_doacao = self.data_ultima_doacao()
        intervalo_dias = INTERVALO_DIAS_DOACAO[self.sexo]
        limite_anual = LIMITE_DOACOES_ANO[self.sexo]

        if ultima_doacao:
            candidatas.append(ultima_doacao + timedelta(days=intervalo_dias))

        if self.data_ultimo_parto:
            limite_dias = DIAS_POS_PARTO_CESAREA if self.parto_cesarea else DIAS_POS_PARTO_NORMAL
            candidatas.append(self.data_ultimo_parto + timedelta(days=limite_dias))

        if self.doacoes_ultimos_12_meses() >= limite_anual:
            doacoes_recentes = list(self.historico.order_by('-data_doacao')[:limite_anual])
            if doacoes_recentes:
                mais_antiga = doacoes_recentes[-1].data_doacao
                candidatas.append(mais_antiga + timedelta(days=365))

        return max(candidatas)


class HistoricoDoacao(models.Model):
    doador = models.ForeignKey(Doador, on_delete=models.CASCADE, related_name='historico')
    data_doacao = models.DateField()
    local = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de doação'
        verbose_name_plural = 'Histórico de doações'
        ordering = ['-data_doacao']

    def __str__(self):
        return f'{self.doador.nome_completo} - {self.data_doacao}'


class Agendamento(models.Model):

    class Status(models.TextChoices):
        CONFIRMADO = 'confirmado', 'Confirmado'
        CONCLUIDO = 'concluido', 'Concluído'
        CANCELADO = 'cancelado', 'Cancelado'

    doador = models.ForeignKey(Doador, on_delete=models.CASCADE, related_name='agendamentos')
    hemocentro = models.ForeignKey(Hemocentro, on_delete=models.CASCADE, related_name='agendamentos')
    data = models.DateField()
    horario = models.CharField(max_length=5, help_text='Ex: 09:30')
    observacoes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.CONFIRMADO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento de doação'
        verbose_name_plural = 'Agendamentos de doação'
        ordering = ['data', 'horario']

    def __str__(self):
        return f'{self.doador.nome_completo} em {self.hemocentro.nome} ({self.data} às {self.horario})'
