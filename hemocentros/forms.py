from django import forms

from hemoconecta.utilitarios import TIPOS_SANGUINEOS, normalizar_cnpj

from .models import Hemocentro

CLASSE_CAMPO = 'form-control'


def validar_cnpj_do_formulario(valor, ignorar_pk=None):
    if not valor:
        return ''
    cnpj = normalizar_cnpj(valor)
    if cnpj is None:
        raise forms.ValidationError('CNPJ inválido. Confira os números digitados.')
    outros = Hemocentro.objects.filter(cnpj=cnpj)
    if ignorar_pk:
        outros = outros.exclude(pk=ignorar_pk)
    if outros.exists():
        raise forms.ValidationError('Este CNPJ já está cadastrado.')
    return cnpj


class FormularioCadastroHemocentro(forms.Form):
    username = forms.CharField(label='Usuário', max_length=150, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': CLASSE_CAMPO}))
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': CLASSE_CAMPO}))
    password2 = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput(attrs={'class': CLASSE_CAMPO}))

    nome = forms.CharField(label='Nome do hemocentro', max_length=200, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    cnpj = forms.CharField(label='CNPJ', max_length=18, required=False, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    descricao = forms.CharField(label='Descrição', required=False, widget=forms.Textarea(attrs={'class': CLASSE_CAMPO, 'rows': 3}))
    telefone = forms.CharField(label='Telefone', max_length=20, required=False, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    horario_funcionamento = forms.CharField(label='Horário de funcionamento', widget=forms.Textarea(attrs={'class': CLASSE_CAMPO, 'rows': 2}))

    logradouro = forms.CharField(label='Logradouro', max_length=200, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    numero = forms.CharField(label='Número', max_length=20, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    bairro = forms.CharField(label='Bairro', max_length=100, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    cidade = forms.CharField(label='Cidade', max_length=100, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    estado = forms.ChoiceField(label='Estado', choices=Hemocentro.estado.field.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    cep = forms.CharField(label='CEP', max_length=9, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))

    def clean_cnpj(self):
        return validar_cnpj_do_formulario(self.cleaned_data.get('cnpj'))

    def clean_username(self):
        from usuarios.models import Usuario
        username = self.cleaned_data['username']
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean_email(self):
        from usuarios.models import Usuario
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        dados_limpos = super().clean()
        senha1 = dados_limpos.get('password1')
        senha2 = dados_limpos.get('password2')
        if senha1 and senha2 and senha1 != senha2:
            raise forms.ValidationError('As senhas não coincidem.')
        return dados_limpos


class FormularioEditarHemocentro(forms.ModelForm):
    class Meta:
        model = Hemocentro
        fields = [
            'nome', 'cnpj', 'descricao', 'telefone', 'horario_funcionamento',
            'logradouro', 'numero', 'bairro', 'cidade', 'estado', 'cep',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'cnpj': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'descricao': forms.Textarea(attrs={'class': CLASSE_CAMPO, 'rows': 3}),
            'telefone': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'horario_funcionamento': forms.Textarea(attrs={'class': CLASSE_CAMPO, 'rows': 2}),
            'logradouro': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'numero': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'bairro': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'cidade': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'cep': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
        }

    def clean_cnpj(self):
        return validar_cnpj_do_formulario(self.cleaned_data.get('cnpj'), ignorar_pk=self.instance.pk)


def nome_do_campo_estoque(tipo_sanguineo):
    return 'tipo_' + tipo_sanguineo.replace('+', 'pos').replace('-', 'neg')


class FormularioEstoque(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for tipo, rotulo in TIPOS_SANGUINEOS:
            self.fields[nome_do_campo_estoque(tipo)] = forms.IntegerField(
                label=rotulo,
                min_value=0,
                max_value=9999,
                widget=forms.NumberInput(attrs={'class': CLASSE_CAMPO}),
            )
