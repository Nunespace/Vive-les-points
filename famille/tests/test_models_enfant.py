import pytest
from django.db import IntegrityError
from famille.models import Enfant


@pytest.mark.django_db
def test_enfant_defaults_and_str(famille):
    e = Enfant.objects.create(prenom="Léo", famille=famille)
    assert e.solde_points == 0  # default
    assert str(e) == "Léo 0"


@pytest.mark.django_db
def test_enfant_user_optional_nullable(famille):
    # user est optionnel (null=True, blank=True)
    e = Enfant.objects.create(prenom="Zoé", famille=famille, user=None)
    assert e.user is None


@pytest.mark.django_db
def test_enfant_user_set_and_set_null_on_user_delete(famille, enfant_user):
    e = Enfant.objects.create(prenom="Tom", famille=famille, user=enfant_user)
    assert e.user_id == enfant_user.id

    # Supprimer le user -> SET_NULL
    enfant_user.delete()
    e.refresh_from_db()
    assert e.user is None


@pytest.mark.django_db
def test_enfant_user_one_to_one_uniqueness(famille, autre_famille, enfant_user):
    # Premier enfant lié au user
    Enfant.objects.create(prenom="A", famille=famille, user=enfant_user)

    # Second enfant ne peut pas réutiliser le même user (OneToOne)
    with pytest.raises(IntegrityError):
        Enfant.objects.create(prenom="B", famille=autre_famille, user=enfant_user)


@pytest.mark.django_db
def test_enfant_foreign_key_to_famille_cascade(famille):
    e = Enfant.objects.create(prenom="Inès", famille=famille)
    pk = e.pk
    famille.delete()
    assert not Enfant.objects.filter(pk=pk).exists()
