# famille/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm
from .models import Famille, Enfant


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe'
        })
    )


class FamilleForm(forms.ModelForm):
    class Meta:
        model = Famille
        fields = ["nom", "is_first_login"]  # 'user' sera fixé dans la vue
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom de la famille"}),
            "is_first_login": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


EnfantFormSet = inlineformset_factory(
    Famille,
    Enfant,
    fields=["prenom", "solde_points"],
    extra=1,
    can_delete=True,
    widgets={
        "prenom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom"}),
        "solde_points": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0"}),
    },
)
