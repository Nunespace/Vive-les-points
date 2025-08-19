import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from famille.models import Famille, UserProfile, Enfant

# ... ton conftest actuel ...

User = get_user_model()


@pytest.fixture
def famille():
    return Famille.objects.create(nom="Dupont")


@pytest.fixture
def autre_famille():
    return Famille.objects.create(nom="Martin")


@pytest.fixture
def parent_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="parent1",
        email="parent1@example.com",
        password="pwd",
        first_name="Jean",
        last_name="Dupont",
    )


@pytest.fixture
def autre_parent_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="parent2",
        email="parent2@example.com",
        password="pwd",
        first_name="Marie",
        last_name="Dupont",
    )


@pytest.fixture
def enfant_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="enfant1",
        email="enfant1@example.com",
        password="pwd",
        first_name="Léa",
        last_name="Dupont",
    )


@pytest.fixture
def userprofile_parent(famille, parent_user):
    return UserProfile.objects.create(
        user=parent_user, famille=famille, role="parent"
    )


@pytest.fixture
def enfant(famille):
    return Enfant.objects.create(
        prenom="Léa", famille=famille
    )  # solde_points par défaut


@pytest.fixture
def userprofile_enfant(famille, enfant_user):
    return UserProfile.objects.create(
        user=enfant_user, famille=famille, role="enfant"
    )


@pytest.fixture
def give_perms():
    """
    Utilitaire: attribue une liste de permissions (par codenames) à un utilisateur.
    Usage: give_perms(user, ["points.view_pointpositif", ...])
    """

    def _give(user, codenames):
        perms = Permission.objects.filter(
            codename__in=[c.split(".")[-1] for c in codenames]
        )
        for p in perms:
            user.user_permissions.add(p)
        user.refresh_from_db()
        return user

    return _give
