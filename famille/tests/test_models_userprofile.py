import pytest
from django.core.exceptions import ValidationError
from famille.models import UserProfile


@pytest.mark.django_db
def test_userprofile_str_uses_full_name_family_and_role(userprofile_parent):
    s = str(userprofile_parent)
    # get_full_name() = "Jean Dupont" via fixture
    assert "Jean Dupont" in s
    assert "(parent)" in s
    assert "Dupont" in s  # famille


@pytest.mark.django_db
def test_userprofile_related_name_profile_on_user(userprofile_parent, parent_user):
    # L'accès inverse fonctionne
    assert parent_user.profile == userprofile_parent


@pytest.mark.django_db
def test_userprofile_role_choices_validation(parent_user, famille):
    up = UserProfile(user=parent_user, famille=famille, role="invalide")
    with pytest.raises(ValidationError):
        up.full_clean()  # doit lever sur choices non valides


@pytest.mark.django_db
def test_userprofile_cascade_delete_on_user(userprofile_parent, parent_user):
    # Sanity
    pk = userprofile_parent.pk
    assert UserProfile.objects.filter(pk=pk).exists()

    # Supprimer l'utilisateur doit supprimer le profil (CASCADE)
    parent_user.delete()
    assert not UserProfile.objects.filter(pk=pk).exists()
