from django import forms
from django.contrib.auth import forms as auth_forms
from crispy_forms.helper import FormHelper
from .models import Enfant, Point_negatif, Point_positif
from .form_layouts import PointsPositifsCreationLayout, PointsNegatifsCreationLayout
from django.contrib.auth.forms import AuthenticationForm


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


class PointsPositifsCreationForm(forms.ModelForm):
    """Formulaire de création pour les points positifs."""

    class Meta:
        model = Point_positif

        fields = (
            "nb_positif",
            "motif1",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = PointsPositifsCreationLayout()


class PointsNegatifsCreationForm(forms.ModelForm):
    """Formulaire de création pour les points positifs."""

    class Meta:
        model = Point_negatif

        fields = (
            "nb_negatif",
            "motif2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = PointsNegatifsCreationLayout()
