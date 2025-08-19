import pytest
from datetime import date
from django.utils import timezone
from django.forms import DateInput

from points.forms import (
    PointsPositifsCreationForm,
    PointsNegatifsCreationForm,
    PointPositifEditForm,
    PointNegatifEditForm,
    PointPositifFormSet,
    PointNegatifFormSet,
    ISO_FMT,
)
from points.models import PointPositif, PointNegatif
from points.form_layouts import (
    PointsPositifsCreationLayout,
    PointsNegatifsCreationLayout,
)


# ---------------------------
# Forms de création (crispy)
# ---------------------------
def test_points_positifs_creation_form_structure():
    form = PointsPositifsCreationForm()
    # champs présents
    assert set(form.fields.keys()) == {"nb_positif", "motif1"}
    # widgets / classes
    assert "form-control" in form.fields["nb_positif"].widget.attrs.get(
        "class", ""
    )
    assert "form-control" in form.fields["motif1"].widget.attrs.get(
        "class", ""
    )
    # crispy helper / layout
    assert hasattr(form, "helper")
    assert form.helper.form_tag is False
    assert isinstance(form.helper.layout, PointsPositifsCreationLayout)


def test_points_negatifs_creation_form_structure():
    form = PointsNegatifsCreationForm()
    assert set(form.fields.keys()) == {"nb_negatif", "motif2"}
    assert "form-control" in form.fields["nb_negatif"].widget.attrs.get(
        "class", ""
    )
    assert "form-control" in form.fields["motif2"].widget.attrs.get(
        "class", ""
    )
    assert hasattr(form, "helper")
    assert form.helper.form_tag is False
    assert isinstance(form.helper.layout, PointsNegatifsCreationLayout)


@pytest.mark.django_db
def test_points_positifs_creation_form_save_with_enfant(enfant):
    data = {"nb_positif": 4, "motif1": "Devoirs faits"}
    form = PointsPositifsCreationForm(data=data)
    assert form.is_valid(), form.errors

    # commit=False car l'FK enfant n'est pas dans le form
    instance = form.save(commit=False)
    instance.enfant = enfant
    instance.save()

    instance.refresh_from_db()
    assert instance.nb_positif == 4
    assert instance.motif1 == "Devoirs faits"
    assert instance.enfant == enfant


@pytest.mark.django_db
def test_points_negatifs_creation_form_save_with_enfant(enfant):
    data = {"nb_negatif": 2, "motif2": "Bêtise"}
    form = PointsNegatifsCreationForm(data=data)
    assert form.is_valid(), form.errors

    instance = form.save(commit=False)
    instance.enfant = enfant
    instance.save()

    instance.refresh_from_db()
    assert instance.nb_negatif == 2
    assert instance.motif2 == "Bêtise"
    assert instance.enfant == enfant


# ---------------------------
# Forms d'édition (mixins ISO)
# ---------------------------
# ✅ plus robuste : on ne vérifie pas attrs["type"], seulement la nature du widget et l'initial
def test_point_positif_edit_form_date_widget_and_initial():
    form = PointPositifEditForm()
    w = form.fields["date"].widget
    assert isinstance(w, DateInput)

    # Vérifie que l'input rendu contient la date du jour au format ISO
    rendered = str(form["date"])
    today_iso = timezone.localdate().strftime(ISO_FMT)
    assert today_iso in rendered  # ex: value="2025-08-19"


def test_point_negatif_edit_form_fields_and_widgets():
    form = PointNegatifEditForm()
    # champs présents
    assert set(form.fields.keys()) == {"date", "nb_negatif", "motif2"}
    assert "form-control-sm" in form.fields["nb_negatif"].widget.attrs.get(
        "class", ""
    )
    assert "form-control-sm" in form.fields["motif2"].widget.attrs.get(
        "class", ""
    )


@pytest.mark.django_db
def test_point_positif_edit_form_accepts_iso_date(enfant):
    d = timezone.localdate().strftime(ISO_FMT)
    form = PointPositifEditForm(
        data={"date": d, "nb_positif": 3, "motif1": "OK"}
    )
    assert form.is_valid(), form.errors
    # la valeur est parsée en objet date
    assert form.cleaned_data["date"] == timezone.localdate()


# ✅ on vérifie que l'ISO est bien accepté et parsé en date python
@pytest.mark.django_db
def test_point_negatif_edit_form_accepts_iso_date():
    iso = timezone.localdate().strftime(ISO_FMT)  # "YYYY-MM-DD"
    form = PointNegatifEditForm(
        data={"date": iso, "nb_negatif": 1, "motif2": "X"}
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["date"] == timezone.localdate()


# ---------------------------
# ModelFormSets (historique)
# ---------------------------
@pytest.mark.django_db
def test_point_positif_formset_update_and_delete(enfant):
    # Préparer 2 lignes pour l'enfant (avec date déjà "date" pour éviter les histoires datetime)
    p1 = PointPositif.objects.create(
        enfant=enfant, nb_positif=1, motif1="A", date=timezone.localdate()
    )
    p2 = PointPositif.objects.create(
        enfant=enfant, nb_positif=2, motif1="B", date=timezone.localdate()
    )

    qs = PointPositif.objects.filter(enfant=enfant).order_by("id")

    # Management form pour 2 formulaires initiaux
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        # form-0 (update)
        "form-0-id": str(p1.id),
        "form-0-date": timezone.localdate().strftime(ISO_FMT),
        "form-0-nb_positif": "5",
        "form-0-motif1": "A+",
        "form-0-DELETE": "",
        # form-1 (demande suppression)
        "form-1-id": str(p2.id),
        "form-1-date": timezone.localdate().strftime(ISO_FMT),
        "form-1-nb_positif": "2",
        "form-1-motif1": "B",
        "form-1-DELETE": "on",
    }

    fs = PointPositifFormSet(data=data, queryset=qs)
    assert fs.is_valid(), fs.errors

    cd0 = fs.forms[0].cleaned_data
    cd1 = fs.forms[1].cleaned_data

    assert cd0["nb_positif"] == 5
    assert cd0["motif1"] == "A+"
    assert cd0["DELETE"] is False

    assert cd1["DELETE"] is True


@pytest.mark.django_db
def test_point_negatif_formset_update_and_delete(enfant):
    n1 = PointNegatif.objects.create(
        enfant=enfant, nb_negatif=1, motif2="X", date=timezone.localdate()
    )
    n2 = PointNegatif.objects.create(
        enfant=enfant, nb_negatif=3, motif2="Y", date=timezone.localdate()
    )

    qs = PointNegatif.objects.filter(enfant=enfant).order_by("id")

    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "2",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        # update
        "form-0-id": str(n1.id),
        "form-0-date": timezone.localdate().strftime(ISO_FMT),
        "form-0-nb_negatif": "4",
        "form-0-motif2": "X-",
        "form-0-DELETE": "",
        # delete
        "form-1-id": str(n2.id),
        "form-1-date": timezone.localdate().strftime(ISO_FMT),
        "form-1-nb_negatif": "3",
        "form-1-motif2": "Y",
        "form-1-DELETE": "on",
    }

    fs = PointNegatifFormSet(data=data, queryset=qs)
    assert fs.is_valid(), fs.errors

    cd0 = fs.forms[0].cleaned_data
    cd1 = fs.forms[1].cleaned_data

    assert cd0["nb_negatif"] == 4
    assert cd0["motif2"] == "X-"
    assert cd0["DELETE"] is False

    assert cd1["DELETE"] is True
