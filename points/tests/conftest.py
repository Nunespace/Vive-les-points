import pytest
from django.contrib.auth.models import Permission

# Rend disponibles les fixtures de l'app famille (famille, enfant, parent_user, etc.)
pytest_plugins = ["famille.tests.conftest"]


@pytest.fixture
def give_perms():
    """
    Utilitaire: attribue une liste de permissions (par codenames) à un utilisateur.
    Usage: give_perms(user, ["points.view_pointpositif", ...])
    """
    def _give(user, codenames):
        perms = Permission.objects.filter(codename__in=[c.split(".")[-1] for c in codenames])
        for p in perms:
            user.user_permissions.add(p)
        user.refresh_from_db()
        return user
    return _give
