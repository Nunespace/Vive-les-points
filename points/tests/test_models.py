import pytest
from django.utils import timezone
from points.models import (
    BaremeRecompense,
    BaremePointPositif,
    BaremePointNegatif,
    PointPositif,
    PointNegatif,
)


# -----------------------
# Barèmes
# -----------------------
@pytest.mark.django_db
def test_bareme_recompense_str():
    b = BaremeRecompense.objects.create(
        points=10, valeur_euros="5 €", valeur_temps="30 min"
    )
    assert str(b) == "10 points"


@pytest.mark.django_db
def test_bareme_point_positif_defaults_and_str():
    b = BaremePointPositif.objects.create(motif="Devoirs faits")
    assert b.points == 1  # default
    assert str(b) == "Devoirs faits"


@pytest.mark.django_db
def test_bareme_point_negatif_defaults_and_str():
    b = BaremePointNegatif.objects.create(motif="Bêtise")
    assert b.points == -1  # default
    assert str(b) == "Bêtise"


# -----------------------
# Points positifs/négatifs
# -----------------------


@pytest.mark.django_db
def test_point_positif_defaults_and_str(enfant):
    p = PointPositif.objects.create(enfant=enfant, nb_positif=3)
    p.refresh_from_db()  # <-- important
    assert p.date == timezone.localdate()
    s = str(p)
    assert enfant.prenom in s
    assert "3" in s
    assert str(p.date) in s


@pytest.mark.django_db
def test_point_negatif_defaults_and_str(enfant):
    n = PointNegatif.objects.create(enfant=enfant, nb_negatif=2)
    n.refresh_from_db()  # <-- important
    assert n.date == timezone.localdate()
    s = str(n)
    assert enfant.prenom in s
    assert "2" in s
    assert str(n.date) in s


@pytest.mark.django_db
def test_points_cascade_on_enfant_delete(enfant):
    p = PointPositif.objects.create(enfant=enfant, nb_positif=1)
    n = PointNegatif.objects.create(enfant=enfant, nb_negatif=1)
    pk_p, pk_n = p.pk, n.pk

    # suppression de l'enfant -> cascade sur ses points
    enfant.delete()
    assert not PointPositif.objects.filter(pk=pk_p).exists()
    assert not PointNegatif.objects.filter(pk=pk_n).exists()
