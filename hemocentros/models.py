from django.conf import settings
from django.db import models

from hemoconecta.utilitarios import obter_coordenadas_endereco

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
