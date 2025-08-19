import pytest
from famille.models import Famille, UserProfile, Enfant


@pytest.mark.django_db
def test_famille_str():
    f = Famille.objects.create(nom="Durand")
    assert str(f) == "Durand"


@pytest.mark.django_db
def test_delete_famille_cascade_on_userprofile_and_enfant(famille, parent_user, enfant):
    # Arrange
    up = UserProfile.objects.create(user=parent_user, famille=famille, role="parent")
    # Sanity
    assert UserProfile.objects.filter(pk=up.pk).exists()
    assert Enfant.objects.filter(pk=enfant.pk).exists()

    # Act
    famille.delete()

    # Assert: tout a été supprimé par CASCADE
    assert not UserProfile.objects.filter(pk=up.pk).exists()
    assert not Enfant.objects.filter(pk=enfant.pk).exists()
