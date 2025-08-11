# famille/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm
from .models import Famille, Enfant


from django.contrib.auth import get_user_model
from django.forms import formset_factory
from django.forms.widgets import HiddenInput
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Famille, Enfant, UserProfile
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from .models import Famille, Enfant

User = get_user_model()



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
        fields = ["nom"]
        widgets = {"nom": forms.TextInput(attrs={"class": "form-control"})}


class ParentUserForm(forms.Form):
    """Formulaire d'inscription initiale où on crée de zéro tous les comptes : partie famille et parents."""
    first_name = forms.CharField(label="Prénom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Nom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            raise ValidationError("Les mots de passe ne correspondent pas.")
        # Si vous utilisez unique_user_email, cet unique sera géré par l’auth backend.
        # On ajoute néanmoins un check pour feedback immédiat :
        if data.get("email") and User.objects.filter(email__iexact=data["email"]).exists():
            raise ValidationError("Un compte existe déjà avec cet email.")
        return data


class EnfantForm(forms.Form):
    """Formulaire d'inscription initiale où on crée de zéro tous les comptes : partie famille et enfants."""
    prenom = forms.CharField(label="Prénom", max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    solde_points = forms.IntegerField(label="Solde initial", initial=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    # Optionnel : créer aussi un compte utilisateur enfant
    email = forms.EmailField(label="Email (facultatif)", required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Mot de passe (si email saisi)", required=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        data = super().clean()
        email, password = data.get("email"), data.get("password")
        if email:
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError("Un compte existe déjà avec l’email enfant.")
            if not password:
                raise ValidationError("Mot de passe requis si un email enfant est saisi.")
        return data

ParentFormSet = formset_factory(ParentUserForm, extra=1, can_delete=True)
EnfantFormSet = formset_factory(EnfantForm, extra=1, can_delete=True)


class FamilleForm(forms.ModelForm):
    class Meta:
        model = Famille
        fields = ["nom"]
        widgets = {"nom": forms.TextInput(attrs={"class": "form-control"})}


class ParentInlineForm(forms.Form):
    user_id = forms.IntegerField(required=False, widget=HiddenInput)
    first_name = forms.CharField(label="Prénom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name  = forms.CharField(label="Nom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email      = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"class": "form-control"}))
    new_password = forms.CharField(
        label="Nouveau mot de passe (optionnel)", required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    DELETE = forms.BooleanField(required=False)

    def __init__(self, *args, famille=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.famille = famille  # pour validations contextuelles

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user_id = self.cleaned_data.get("user_id")
        qs = User.objects.filter(email__iexact=email)
        if user_id:
            qs = qs.exclude(pk=user_id)
        if qs.exists():
            raise ValidationError("Un compte existe déjà avec cet email.")
        return email

ParentInlineFormSet = formset_factory(ParentInlineForm, extra=0, can_delete=True)


# Enfants : on prend un inline formset lié à Famille
EnfantFormSet = inlineformset_factory(
    Famille, Enfant,
    fields=["prenom", "solde_points"],
    extra=0, can_delete=True,
    widgets={
        "prenom": forms.TextInput(attrs={"class": "form-control"}),
        "solde_points": forms.NumberInput(attrs={"class": "form-control"}),
    },
    labels={
        "DELETE": "Retirer de la famille"
    }
)

class FamilyHardDeleteForm(forms.Form):
    family_name = forms.CharField(
        label="Tapez le nom de la famille pour confirmer",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom exact de la famille"})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )