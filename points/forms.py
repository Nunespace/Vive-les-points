from django import forms
from django.forms import ModelForm, modelformset_factory
from crispy_forms.helper import FormHelper
from .models import PointPositif, PointNegatif
from .form_layouts import PointsPositifsCreationLayout, PointsNegatifsCreationLayout
from django.utils import timezone

ISO_FMT = "%Y-%m-%d"


# ----------- FORMULAIRES CREATION (avec Layout) -----------

class PointsPositifsCreationForm(ModelForm):
    """Formulaire création points positifs (avec crispy layout)"""
    class Meta:
        model = PointPositif
        fields = ("nb_positif", "motif1")
        widgets = {
            "nb_positif": forms.NumberInput(attrs={"class": "form-control"}),
            "motif1": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = PointsPositifsCreationLayout()


class PointsNegatifsCreationForm(ModelForm):
    """Formulaire création points négatifs (avec crispy layout)"""
    class Meta:
        model = PointNegatif
        fields = ("nb_negatif", "motif2")
        widgets = {
            "nb_negatif": forms.NumberInput(attrs={"class": "form-control"}),
            "motif2": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = PointsNegatifsCreationLayout()


# ----------- FORMULAIRES EDITION (pour formsets historiques) -----------

class ISODateMixin:
    """Mixin pour gérer la date au format ISO dans <input type='date'>"""
    date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control form-control-sm"},
            format=ISO_FMT,
        ),
        input_formats=[ISO_FMT],
        initial=timezone.now().date(),
        required=True,
    )


class PointPositifEditForm(ISODateMixin, ModelForm):
    """Formulaire d'édition points positifs (pour formset dans historique)"""
    class Meta:
        model = PointPositif
        fields = ["date", "nb_positif", "motif1"]
        widgets = {
            "nb_positif": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
            "motif1": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }


class PointNegatifEditForm(ISODateMixin, ModelForm):
    """Formulaire d'édition points négatifs (pour formset dans historique)"""
    class Meta:
        model = PointNegatif
        fields = ["date", "nb_negatif", "motif2"]
        widgets = {
            "nb_negatif": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
            "motif2": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }


# ----------- FORMSETS POUR L'HISTORIQUE -----------

PointPositifFormSet = modelformset_factory(
    PointPositif, form=PointPositifEditForm, extra=0, can_delete=True
)

PointNegatifFormSet = modelformset_factory(
    PointNegatif, form=PointNegatifEditForm, extra=0, can_delete=True
)
