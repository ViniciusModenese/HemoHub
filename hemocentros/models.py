from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone

from hemoconecta.utilitarios import TIPOS_SANGUINEOS, obter_coordenadas_endereco

ESTADOS_BRASIL = [
    ('AC', 'AC'), ('AL', 'AL'), ('AP', 'AP'), ('AM', 'AM'), ('BA', 'BA'), ('CE', 'CE'),
    ('DF', 'DF'), ('ES', 'ES'), ('GO', 'GO'), ('MA', 'MA'), ('MT', 'MT'), ('MS', 'MS'),
    ('MG', 'MG'), ('PA', 'PA'), ('PB', 'PB'), ('PR', 'PR'), ('PE', 'PE'), ('PI', 'PI'),
    ('RJ', 'RJ'), ('RN', 'RN'), ('RS', 'RS'), ('RO', 'RO'), ('RR', 'RR'), ('SC', 'SC'),
    ('SP', 'SP'), ('SE', 'SE'), ('TO', 'TO'),
]


class Hemocentro(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hemocentro')
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, blank=True)
    descricao = models.TextField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    horario_funcionamento = models.TextField(help_text='Ex: Segunda a sexta: 08h às 17h')

    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2, choices=ESTADOS_BRASIL)
    cep = models.CharField(max_length=9)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    aprovado = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hemocentro'
        verbose_name_plural = 'Hemocentros'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def endereco_completo(self):
        return f'{self.logradouro}, {self.numero} - {self.bairro}, {self.cidade} - {self.estado}, {self.cep}'

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

    def necessidades_ativas(self):
        return self.necessidades.filter(ativa=True)

    def registrar_entrada_no_estoque(self, tipo_sanguineo, bolsas=1):
        registro, criado = self.estoque.get_or_create(
            tipo_sanguineo=tipo_sanguineo,
            defaults={'quantidade_bolsas': bolsas},
        )
        if not criado:
            self.estoque.filter(pk=registro.pk).update(
                quantidade_bolsas=F('quantidade_bolsas') + bolsas,
                atualizado_em=timezone.now(),
            )


class FotoHemocentro(models.Model):
    hemocentro = models.ForeignKey(Hemocentro, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='hemocentros/')
    legenda = models.CharField(max_length=150, blank=True)
    enviada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto do hemocentro'
        verbose_name_plural = 'Fotos do hemocentro'
        ordering = ['enviada_em']

    def __str__(self):
        return f'Foto de {self.hemocentro.nome}'


ESTOQUE_NIVEL_CRITICO = 10
ESTOQUE_NIVEL_BAIXO = 25
ESTOQUE_REFERENCIA_BARRA = 60


class EstoqueSanguineo(models.Model):
    hemocentro = models.ForeignKey(Hemocentro, on_delete=models.CASCADE, related_name='estoque')
    tipo_sanguineo = models.CharField(max_length=3, choices=TIPOS_SANGUINEOS)
    quantidade_bolsas = models.PositiveIntegerField(default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estoque de sangue'
        verbose_name_plural = 'Estoques de sangue'
        ordering = ['tipo_sanguineo']
        constraints = [
            models.UniqueConstraint(fields=['hemocentro', 'tipo_sanguineo'], name='estoque_unico_por_tipo'),
        ]

    def __str__(self):
        return f'{self.hemocentro.nome} - {self.tipo_sanguineo}: {self.quantidade_bolsas} bolsas'

    @property
    def nivel(self):
        return nivel_do_estoque(self.quantidade_bolsas)

    @property
    def percentual(self):
        return min(100, round(self.quantidade_bolsas * 100 / ESTOQUE_REFERENCIA_BARRA))


def nivel_do_estoque(quantidade):
    if quantidade < ESTOQUE_NIVEL_CRITICO:
        return 'critico'
    if quantidade < ESTOQUE_NIVEL_BAIXO:
        return 'baixo'
    return 'normal'
