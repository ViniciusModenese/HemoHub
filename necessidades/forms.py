from django import forms

from .models import NecessidadeSanguinea


class FormularioNecessidade(forms.ModelForm):
    class Meta:
        model = NecessidadeSanguinea
        fields = ['tipo_sanguineo', 'nivel_urgencia', 'quantidade_bolsas', 'observacoes']
        widgets = {
            'tipo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'nivel_urgencia': forms.Select(attrs={'class': 'form-select'}),
            'quantidade_bolsas': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
