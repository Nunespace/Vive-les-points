# famille/tests/test_forms.py
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from famille.forms import (
    EmailAuthenticationForm,
    FamilleForm,
    ParentUserForm,
    EnfantSignupForm,
    ParentFormSet,
    EnfantSignupFormSet,
    ParentInlineForm,
    EnfantManageForm,
    FamilyHardDeleteForm,
)
from famille.models import Enfant, UserProfile

User = get_user_model()


# -----------------------
# EmailAuthenticationForm
# -----------------------
def test_email_authentication_form_fields_and_widgets():
    form = EmailAuthenticationForm()
    # Champs présents
    assert "username" in form.fields
    assert "password" in form.fields
    # Types
    assert form.fields["username"].__class__.__name__ == "EmailField"
    # Widgets / attrs
    u_widget = form.fields["username"].widget
    p_widget = form.fields["password"].widget
    assert "form-control" in u_widget.attrs.get("class", "")
    assert "form-control" in p_widget.attrs.get("class", "")
    assert u_widget.attrs.get("placeholder") == "Votre adresse email"
    assert p_widget.attrs.get("placeholder") == "Votre mot de passe"


# ------------
# FamilleForm
# ------------
@pytest.mark.django_db
def test_famille_form_valid(famille):
    form = FamilleForm(data={"nom": "Durand"})
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_famille_form_invalid_when_missing_name():
    form = FamilleForm(data={"nom": ""})
    assert not form.is_valid()
    assert "nom" in form.errors


# ---------------
# ParentUserForm
# ---------------
@pytest.mark.django_db
def test_parent_user_form_password_mismatch():
    form = ParentUserForm(
        data={
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean@example.com",
            "password1": "a",
            "password2": "b",
        }
    )
    assert not form.is_valid()
    assert "Les mots de passe ne correspondent pas." in form.non_field_errors()


@pytest.mark.django_db
def test_parent_user_form_email_already_exists(parent_user):
    # parent_user fixture a déjà un email = parent1@example.com
    form = ParentUserForm(
        data={
            "first_name": "Marie",
            "last_name": "Dupont",
            "email": "parent1@example.com",
            "password1": "pwd",
            "password2": "pwd",
        }
    )
    assert not form.is_valid()
    assert "Un compte existe déjà avec cet email." in form.non_field_errors()


@pytest.mark.django_db
def test_parent_user_form_valid_when_unique_email():
    form = ParentUserForm(
        data={
            "first_name": "Alice",
            "last_name": "Martin",
            "email": "alice@example.com",
            "password1": "pwd",
            "password2": "pwd",
        }
    )
    assert form.is_valid(), form.errors


# ------------------
# EnfantSignupForm
# ------------------
@pytest.mark.django_db
def test_enfant_signup_requires_password_if_email():
    form = EnfantSignupForm(
        data={
            "prenom": "Léo",
            "solde_points": 0,
            "email": "enfant@example.com",
            "password": "",
        }
    )
    assert not form.is_valid()
    assert "Mot de passe requis si un email enfant est saisi." in form.non_field_errors()


@pytest.mark.django_db
def test_enfant_signup_email_already_linked_to_other_enfant(famille, enfant_user):
    # L'email existe et est déjà lié à un Enfant
    Enfant.objects.create(prenom="DéjàLié", famille=famille, user=enfant_user)

    form = EnfantSignupForm(
        data={
            "prenom": "Tom",
            "solde_points": 0,
            "email": enfant_user.email,  # déjà utilisé par un enfant
            "password": "pwd",
        }
    )
    assert not form.is_valid()
    assert "Cet email est déjà utilisé par un autre enfant." in form.non_field_errors()


@pytest.mark.django_db
def test_enfant_signup_valid_without_email():
    form = EnfantSignupForm(data={"prenom": "Zoé", "solde_points": 3})
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_enfant_signup_valid_with_existing_user_not_linked(famille):
    # Un user existe avec cet email mais n'est pas lié à un Enfant → OK
    u = User.objects.create_user(username="x", email="libre@example.com", password="pwd")
    assert not Enfant.objects.filter(user=u).exists()

    form = EnfantSignupForm(
        data={
            "prenom": "Nina",
            "solde_points": 0,
            "email": "libre@example.com",
            "password": "pwd",
        }
    )
    assert form.is_valid(), form.errors


# -------------------
# Helpers formset data
# -------------------
def _fs_mgmt(prefix, total, initial=0):
    # Management form keys
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


# ----------------
# ParentFormSet
# ----------------
@pytest.mark.django_db
def test_parent_formset_requires_at_least_one_parent():
    # 1 formulaire rempli mais marqué DELETE => doit déclencher le non_form_error
    prefix = "form"
    data = {
        **_fs_mgmt(prefix, total=1, initial=0),
        f"{prefix}-0-first_name": "Jean",
        f"{prefix}-0-last_name": "Dupont",
        f"{prefix}-0-email": "jean@example.com",
        f"{prefix}-0-password1": "pwd",
        f"{prefix}-0-password2": "pwd",
        f"{prefix}-0-DELETE": "on",  # supprimé → ne compte pas
    }
    fs = ParentFormSet(data=data, prefix=prefix)
    assert not fs.is_valid()
    assert "Ajoutez au moins un parent." in fs.non_form_errors()


@pytest.mark.django_db
def test_parent_formset_valid_with_one_parent():
    prefix = "form"
    data = {
        **_fs_mgmt(prefix, total=1, initial=0),
        f"{prefix}-0-first_name": "Alice",
        f"{prefix}-0-last_name": "Martin",
        f"{prefix}-0-email": "alice@example.com",
        f"{prefix}-0-password1": "pwd",
        f"{prefix}-0-password2": "pwd",
        # pas de DELETE
    }
    fs = ParentFormSet(data=data, prefix=prefix)
    assert fs.is_valid(), fs.errors


# ----------------------
# EnfantSignupFormSet
# ----------------------
@pytest.mark.django_db
def test_enfant_signup_formset_requires_at_least_one_enfant():
    prefix = "form"
    data = {
        **_fs_mgmt(prefix, total=1, initial=0),
        f"{prefix}-0-prenom": "Léa",
        f"{prefix}-0-solde_points": "0",
        f"{prefix}-0-email": "",
        f"{prefix}-0-password": "",
        f"{prefix}-0-DELETE": "on",  # supprimé → ne compte pas
    }
    fs = EnfantSignupFormSet(data=data, prefix=prefix)
    assert not fs.is_valid()
    assert "Ajoutez au moins un enfant." in fs.non_form_errors()


@pytest.mark.django_db
def test_enfant_signup_formset_valid_with_one_enfant():
    prefix = "form"
    data = {
        **_fs_mgmt(prefix, total=1, initial=0),
        f"{prefix}-0-prenom": "Nina",
        f"{prefix}-0-solde_points": "2",
        f"{prefix}-0-email": "",
        f"{prefix}-0-password": "",
    }
    fs = EnfantSignupFormSet(data=data, prefix=prefix)
    assert fs.is_valid(), fs.errors


# -------------------
# ParentInlineForm
# -------------------
@pytest.mark.django_db
def test_parent_inline_form_rejects_duplicate_email_for_other_user(famille, parent_user, autre_parent_user):
    # Tenter de créer un parent avec l'email de parent_user → refus
    form = ParentInlineForm(
        data={
            "user_id": "",
            "first_name": "X",
            "last_name": "Y",
            "email": parent_user.email,
            "new_password": "",
            "DELETE": False,
        },
        famille=famille,
    )
    assert not form.is_valid()
    assert "Un compte existe déjà avec cet email." in form.errors["email"]


@pytest.mark.django_db
def test_parent_inline_form_allows_same_email_for_self(famille, parent_user):
    # Mise à jour "soi-même" => autorisé
    form = ParentInlineForm(
        data={
            "user_id": parent_user.pk,
            "first_name": parent_user.first_name,
            "last_name": parent_user.last_name,
            "email": parent_user.email,  # même email
            "new_password": "",
            "DELETE": False,
        },
        famille=famille,
    )
    assert form.is_valid(), form.errors


# -------------------
# EnfantManageForm
# -------------------
@pytest.mark.django_db
def test_enfant_manage_prefills_email_when_user_linked(famille, enfant_user):
    enfant = Enfant.objects.create(prenom="Léa", famille=famille, user=enfant_user)
    form = EnfantManageForm(instance=enfant)
    assert form.fields["email"].initial == enfant_user.email


@pytest.mark.django_db
def test_enfant_manage_clean_duplicate_email_other_user(famille, enfant):
    other = User.objects.create_user(username="o", email="dup@example.com", password="pwd")
    assert enfant.user is None
    form = EnfantManageForm(
        data={"prenom": enfant.prenom, "solde_points": enfant.solde_points, "email": "dup@example.com", "new_password": "pwd"},
        instance=enfant,
    )
    # L'email existe déjà sur un autre user ⇒ message "Un compte utilisateur..."
    assert not form.is_valid()
    assert "Un compte utilisateur existe déjà avec cet email." in form.non_field_errors()


@pytest.mark.django_db
def test_enfant_manage_clean_requires_password_when_new_email_and_no_user(famille, enfant):
    form = EnfantManageForm(
        data={"prenom": enfant.prenom, "solde_points": enfant.solde_points, "email": "newchild@example.com", "new_password": ""},
        instance=enfant,
    )
    assert not form.is_valid()
    assert "Mot de passe requis si un email enfant est saisi." in form.non_field_errors()


@pytest.mark.django_db
def test_enfant_manage_save_user_creates_new_user_and_profile(famille, enfant):
    data = {
        "prenom": enfant.prenom,
        "solde_points": enfant.solde_points,
        "email": "child@example.com",
        "new_password": "pwd",
    }
    form = EnfantManageForm(data=data, instance=enfant)
    assert form.is_valid(), form.errors

    form.save_user(famille=famille)
    enfant.refresh_from_db()
    assert enfant.user is not None
    u = enfant.user
    assert u.email == "child@example.com"
    assert u.username == "child@example.com"

    # Groupe "enfant"
    assert u.groups.filter(name="enfant").exists()
    # UserProfile créé / MAJ
    up = UserProfile.objects.get(user=u)
    assert up.role == "enfant"
    assert up.famille == famille


@pytest.mark.django_db
def test_enfant_manage_save_user_updates_existing_user_and_password(famille, enfant_user):
    enfant = Enfant.objects.create(prenom="Tom", famille=famille, user=enfant_user)
    data = {
        "prenom": enfant.prenom,
        "solde_points": enfant.solde_points,
        "email": "newmail@example.com",
        "new_password": "newpwd",
    }
    form = EnfantManageForm(data=data, instance=enfant)
    assert form.is_valid(), form.errors

    form.save_user(famille=famille)
    enfant.refresh_from_db()
    u = enfant.user
    assert u.email == "newmail@example.com"
    assert u.username == "newmail@example.com"
    assert u.check_password("newpwd")

    # Profil mis à jour
    up = UserProfile.objects.get(user=u)
    assert up.role == "enfant"
    assert up.famille == famille
    assert u.groups.filter(name="enfant").exists()


@pytest.mark.django_db
def test_enfant_manage_save_user_removes_account_if_email_empty(famille, enfant_user):
    enfant = Enfant.objects.create(prenom="Inès", famille=famille, user=enfant_user)
    user_id = enfant_user.id

    data = {"prenom": enfant.prenom, "solde_points": enfant.solde_points, "email": "", "new_password": ""}
    form = EnfantManageForm(data=data, instance=enfant)
    assert form.is_valid(), form.errors

    form.save_user(famille=famille)
    enfant.refresh_from_db()
    assert enfant.user is None
    assert not User.objects.filter(pk=user_id).exists()


# -----------------------
# FamilyHardDeleteForm
# -----------------------
def test_family_hard_delete_form_fields_and_widgets():
    form = FamilyHardDeleteForm()
    assert "family_name" in form.fields
    assert "password" in form.fields
    assert "form-control" in form.fields["family_name"].widget.attrs.get("class", "")
    assert "form-control" in form.fields["password"].widget.attrs.get("class", "")


@pytest.mark.django_db
def test_family_hard_delete_form_valid_submission():
    form = FamilyHardDeleteForm(data={"family_name": "Dupont", "password": "secret"})
    assert form.is_valid(), form.errors
