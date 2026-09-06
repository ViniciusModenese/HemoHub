from django import forms

from hemocentros.models import Hemocentro

from .models import Doador

CLASSE_CAMPO = 'form-control'


class FormularioCadastroDoador(forms.Form):
    username = forms.CharField(label='Usuário', max_length=150, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': CLASSE_CAMPO}))
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': CLASSE_CAMPO}))
    password2 = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput(attrs={'class': CLASSE_CAMPO}))

    nome_completo = forms.CharField(label='Nome completo', max_length=200, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    cpf = forms.CharField(label='CPF', max_length=14, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    data_nascimento = forms.DateField(label='Data de nascimento', widget=forms.DateInput(attrs={'class': CLASSE_CAMPO, 'type': 'date'}))
    sexo = forms.ChoiceField(label='Sexo biológico', choices=Doador.Sexo.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    peso = forms.DecimalField(label='Peso (kg)', max_digits=5, decimal_places=1, widget=forms.NumberInput(attrs={'class': CLASSE_CAMPO}))
    tipo_sanguineo = forms.ChoiceField(label='Tipo sanguíneo', choices=Doador.tipo_sanguineo.field.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    telefone = forms.CharField(label='Telefone', max_length=20, required=False, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))

    esta_gestante = forms.BooleanField(label='Está gestante', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    data_ultimo_parto = forms.DateField(label='Data do último parto', required=False, widget=forms.DateInput(attrs={'class': CLASSE_CAMPO, 'type': 'date'}))
    parto_cesarea = forms.BooleanField(label='O parto foi cesárea', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    logradouro = forms.CharField(label='Logradouro', max_length=200, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    numero = forms.CharField(label='Número', max_length=20, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    bairro = forms.CharField(label='Bairro', max_length=100, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    cidade = forms.CharField(label='Cidade', max_length=100, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))
    estado = forms.ChoiceField(label='Estado', choices=Hemocentro.estado.field.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    cep = forms.CharField(label='CEP', max_length=9, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))

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

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if Doador.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('Este CPF já está cadastrado.')
        return cpf

    def clean(self):
        dados_limpos = super().clean()
        senha1 = dados_limpos.get('password1')
        senha2 = dados_limpos.get('password2')
        if senha1 and senha2 and senha1 != senha2:
            raise forms.ValidationError('As senhas não coincidem.')
        return dados_limpos


class FormularioHistoricoDoacao(forms.Form):
    data_doacao = forms.DateField(label='Data da doação', widget=forms.DateInput(attrs={'class': CLASSE_CAMPO, 'type': 'date'}))
    local = forms.CharField(label='Local', max_length=200, required=False, widget=forms.TextInput(attrs={'class': CLASSE_CAMPO}))


class FormularioEditarDoador(forms.ModelForm):
    class Meta:
        model = Doador
        fields = [
            'nome_completo', 'peso', 'tipo_sanguineo', 'telefone',
            'esta_gestante', 'data_ultimo_parto', 'parto_cesarea',
            'logradouro', 'numero', 'bairro', 'cidade', 'estado', 'cep',
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'peso': forms.NumberInput(attrs={'class': CLASSE_CAMPO}),
            'tipo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'telefone': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'esta_gestante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_ultimo_parto': forms.DateInput(attrs={'class': CLASSE_CAMPO, 'type': 'date'}),
            'parto_cesarea': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logradouro': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'numero': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'bairro': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'cidade': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'cep': forms.TextInput(attrs={'class': CLASSE_CAMPO}),
        }
