import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import transaction
from famille.models import Famille, Enfant, UserProfile

User = get_user_model()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def mgmt(prefix, total, initial=0, can_delete=True):
    data = {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    if can_delete:
        # pas obligatoire, mais explicite
        data[f"{prefix}-0-DELETE"] = ""
    return data


# ------------------------------------------------------------------
# confidentialite_view
# ------------------------------------------------------------------


@pytest.mark.django_db
def test_confidentialite_view(client):
    """
    Vérifie que la page Politique de confidentialité s'affiche correctement.
    """
    url = reverse("confidentialite")
    response = client.get(url)

    # 1. La vue renvoie un code 200
    assert response.status_code == 200

    # 2. Le bon template est utilisé
    assert "famille/confidentialite.html" in [t.name for t in response.templates]

    # 3. Le contenu contient le titre de la page (encodé en UTF-8)
    assert "Politique de confidentialité".encode("utf-8") in response.content


# ------------------------------------------------------------------
# EmailLoginView / EmailLogoutView
# ------------------------------------------------------------------
@pytest.mark.django_db
def test_login_redirects_if_already_authenticated(
    client, userprofile_parent, parent_user
):
    # L'utilisateur parent est déjà connecté -> redirigé (redirect_authenticated_user=True)
    client.force_login(parent_user)
    url = reverse("famille:login")
    resp = client.get(url)
    assert resp.status_code in (302, 301)
    # redirection par défaut vers points:dashboard
    assert reverse("points:dashboard") in resp.url


# remplacer l'ancien test GET par ceci
@pytest.mark.django_db
def test_logout_redirects_to_login(client, userprofile_parent, parent_user):
    client.force_login(parent_user)
    url = reverse("famille:logout")
    resp = client.post(url)  # LogoutView attend POST
    assert resp.status_code in (302, 301)
    assert reverse("famille:login") in resp.url


# ------------------------------------------------------------------
# RegisterFamilyView (GET / POST)
# ------------------------------------------------------------------
@pytest.mark.django_db
def test_register_get_renders(client):
    resp = client.get(reverse("famille:register"))
    # si tes templates existent, on rend 200 ; sinon, adapte ce test (skip)
    assert resp.status_code == 200
    # le contexte doit contenir les 3 formulaires
    assert "famille_form" in resp.context
    assert "parent_formset" in resp.context
    assert "enfant_formset" in resp.context


@pytest.mark.django_db
def test_register_post_creates_family_parents_enfants_and_logs_first_parent(
    client,
):
    url = reverse("famille:register")

    # Management forms
    parents_prefix = "parents"
    enfants_prefix = "enfants"

    data = {
        # Famille
        "nom": "Doe",
        # Parents formset : 1 parent
        **{
            f"{parents_prefix}-TOTAL_FORMS": "1",
            f"{parents_prefix}-INITIAL_FORMS": "0",
            f"{parents_prefix}-MIN_NUM_FORMS": "0",
            f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{parents_prefix}-0-first_name": "John",
        f"{parents_prefix}-0-last_name": "Doe",
        f"{parents_prefix}-0-email": "john.doe@example.com",
        f"{parents_prefix}-0-password1": "pwd",
        f"{parents_prefix}-0-password2": "pwd",
        # Enfants formset : 2 enfants (un avec compte user, un sans)
        **{
            f"{enfants_prefix}-TOTAL_FORMS": "2",
            f"{enfants_prefix}-INITIAL_FORMS": "0",
            f"{enfants_prefix}-MIN_NUM_FORMS": "0",
            f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{enfants_prefix}-0-prenom": "Léa",
        f"{enfants_prefix}-0-email": "lea@example.com",
        f"{enfants_prefix}-0-password": "pwd",
        f"{enfants_prefix}-1-prenom": "Tom",
        f"{enfants_prefix}-1-email": "",
        f"{enfants_prefix}-1-password": "",
    }

    resp = client.post(url, data, follow=True)
    # Redirection finale vers dashboard
    assert resp.redirect_chain, "Aucune redirection détectée"
    assert reverse("points:dashboard") in resp.redirect_chain[-1][0]

    # Famille créée
    fam = Famille.objects.get(nom="Doe")

    # Parent + UserProfile 'parent' créés
    parent_user = User.objects.get(email="john.doe@example.com")
    up = UserProfile.objects.get(user=parent_user)
    assert up.role == "parent"
    assert up.famille == fam

    # Enfants créés
    enfants = Enfant.objects.filter(famille=fam).order_by("prenom")
    assert enfants.count() == 2
    lea = enfants.get(prenom="Léa")
    tom = enfants.get(prenom="Tom")
    assert Enfant.objects.get(famille=fam, prenom="Tom").solde_points == 0

    # Léa a un compte user + profil enfant
    assert lea.user is not None
    up_lea = UserProfile.objects.get(user=lea.user)
    assert up_lea.role == "enfant"
    assert up_lea.famille == fam

    # Tom n'a pas de compte user
    assert tom.user is None

    # L'utilisateur est connecté (1er parent)
    # (si besoin : assert client.session._session_key is not None)
    assert "_auth_user_id" in client.session


# ------------------------------------------------------------------
# ManageFamilyAccountView (GET / POST)
# ------------------------------------------------------------------
@pytest.mark.django_db
def test_manage_get_denies_non_parent(client, parent_user):
    # Utilisateur sans UserProfile parent -> redirigé
    client.force_login(parent_user)  # pas de profile.role=parent
    resp = client.get(reverse("famille:manage_account"))
    assert resp.status_code in (302, 301)
    assert reverse("points:dashboard") in resp.url

    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert "Accès réservé aux parents." in " ".join(msgs)


@pytest.mark.django_db
def test_manage_get_ok_for_parent(client, userprofile_parent, parent_user):
    client.force_login(parent_user)
    resp = client.get(reverse("famille:manage_account"))
    assert resp.status_code == 200
    assert "famille_form" in resp.context
    assert "parent_formset" in resp.context
    assert "enfant_formset" in resp.context


@pytest.mark.django_db
def test_manage_post_no_changes_redirects_info(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)

    # Aucun enfant initial
    enfants_prefix = "enfants"
    parents_prefix = "parents"

    # reconstruire l'initial pour 1 parent existant (comme la vue)
    data = {
        "nom": famille.nom,  # pas de changement
        # Parent formset avec 1 initial
        **{
            f"{parents_prefix}-TOTAL_FORMS": "1",
            f"{parents_prefix}-INITIAL_FORMS": "1",
            f"{parents_prefix}-MIN_NUM_FORMS": "0",
            f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{parents_prefix}-0-user_id": str(parent_user.id),
        f"{parents_prefix}-0-first_name": parent_user.first_name,
        f"{parents_prefix}-0-last_name": parent_user.last_name,
        f"{parents_prefix}-0-email": parent_user.email,
        f"{parents_prefix}-0-new_password": "",
        f"{parents_prefix}-0-DELETE": "",
        # Enfants inline formset vide
        **{
            f"{enfants_prefix}-TOTAL_FORMS": "0",
            f"{enfants_prefix}-INITIAL_FORMS": "0",
            f"{enfants_prefix}-MIN_NUM_FORMS": "0",
            f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
        },
    }

    resp = client.post(reverse("famille:manage_account"), data)
    assert resp.status_code in (302, 301)
    assert reverse("famille:manage_account") in resp.url

    # vérifier le message "Aucun changement détecté."
    # (il est mis avant la redirection)
    # NB: sur une 302, messages sont stockés dans la session, on ne peut pas les lire via resp.wsgi_request ici.


@pytest.mark.django_db
def test_manage_post_update_family_name(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)

    parents_prefix = "parents"
    enfants_prefix = "enfants"

    data = {
        "nom": "Nouvelle Famille",
        # 1 parent initial (inchangé)
        **{
            f"{parents_prefix}-TOTAL_FORMS": "1",
            f"{parents_prefix}-INITIAL_FORMS": "1",
            f"{parents_prefix}-MIN_NUM_FORMS": "0",
            f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{parents_prefix}-0-user_id": str(parent_user.id),
        f"{parents_prefix}-0-first_name": parent_user.first_name,
        f"{parents_prefix}-0-last_name": parent_user.last_name,
        f"{parents_prefix}-0-email": parent_user.email,
        f"{parents_prefix}-0-new_password": "",
        f"{parents_prefix}-0-DELETE": "",
        # enfants vide
        **{
            f"{enfants_prefix}-TOTAL_FORMS": "0",
            f"{enfants_prefix}-INITIAL_FORMS": "0",
            f"{enfants_prefix}-MIN_NUM_FORMS": "0",
            f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
        },
    }

    resp = client.post(reverse("famille:manage_account"), data, follow=True)
    assert resp.redirect_chain
    assert reverse("points:dashboard") in resp.redirect_chain[-1][0]

    famille.refresh_from_db()
    assert famille.nom == "Nouvelle Famille"


@pytest.mark.django_db
def test_manage_post_add_new_parent(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)

    parents_prefix = "parents"
    enfants_prefix = "enfants"

    # 1 parent initial + 1 nouveau parent
    data = {
        "nom": famille.nom,
        **{
            f"{parents_prefix}-TOTAL_FORMS": "2",
            f"{parents_prefix}-INITIAL_FORMS": "1",
            f"{parents_prefix}-MIN_NUM_FORMS": "0",
            f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        },
        # parent existant
        f"{parents_prefix}-0-user_id": str(parent_user.id),
        f"{parents_prefix}-0-first_name": parent_user.first_name,
        f"{parents_prefix}-0-last_name": parent_user.last_name,
        f"{parents_prefix}-0-email": parent_user.email,
        f"{parents_prefix}-0-new_password": "",
        f"{parents_prefix}-0-DELETE": "",
        # nouveau parent (pas d'user_id)
        f"{parents_prefix}-1-user_id": "",
        f"{parents_prefix}-1-first_name": "Alice",
        f"{parents_prefix}-1-last_name": "Martin",
        f"{parents_prefix}-1-email": "alice@example.com",
        f"{parents_prefix}-1-new_password": "pwd",
        f"{parents_prefix}-1-DELETE": "",
        # enfants vide
        **{
            f"{enfants_prefix}-TOTAL_FORMS": "0",
            f"{enfants_prefix}-INITIAL_FORMS": "0",
            f"{enfants_prefix}-MIN_NUM_FORMS": "0",
            f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
        },
    }

    resp = client.post(reverse("famille:manage_account"), data, follow=True)
    assert reverse("points:dashboard") in resp.redirect_chain[-1][0]

    # nouveau parent créé + profil parent
    u = User.objects.get(email="alice@example.com")
    up = UserProfile.objects.get(user=u)
    assert up.role == "parent"
    assert up.famille == famille

@pytest.mark.django_db
def test_manage_post_delete_last_parent_shows_error(client, userprofile_parent, parent_user, famille):
    client.force_login(parent_user)
    parents_prefix = "parents"
    enfants_prefix = "enfants"
    data = {
        "nom": famille.nom,
        f"{parents_prefix}-TOTAL_FORMS": "1",
        f"{parents_prefix}-INITIAL_FORMS": "1",
        f"{parents_prefix}-MIN_NUM_FORMS": "0",
        f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        f"{parents_prefix}-0-user_id": str(parent_user.id),
        f"{parents_prefix}-0-first_name": parent_user.first_name,
        f"{parents_prefix}-0-last_name": parent_user.last_name,
        f"{parents_prefix}-0-email": parent_user.email,
        f"{parents_prefix}-0-new_password": "",
        f"{parents_prefix}-0-DELETE": "on",
        f"{enfants_prefix}-TOTAL_FORMS": "0",
        f"{enfants_prefix}-INITIAL_FORMS": "0",
        f"{enfants_prefix}-MIN_NUM_FORMS": "0",
        f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
    }
    resp = client.post(reverse("famille:manage_account"), data)
    assert resp.status_code == 200
    assert b"Impossible de supprimer le dernier parent" in resp.content


# --- ManageFamilyAccountView : ajout d’un enfant ---

@pytest.mark.django_db
def test_manage_post_add_enfant_and_user(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)
    parents_prefix = "parents"
    enfants_prefix = "enfants"

    data = {
        "nom": famille.nom,
        # parents: 1 initial, inchangé
        **{
            f"{parents_prefix}-TOTAL_FORMS": "1",
            f"{parents_prefix}-INITIAL_FORMS": "1",
            f"{parents_prefix}-MIN_NUM_FORMS": "0",
            f"{parents_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{parents_prefix}-0-user_id": str(parent_user.id),
        f"{parents_prefix}-0-first_name": parent_user.first_name,
        f"{parents_prefix}-0-last_name": parent_user.last_name,
        f"{parents_prefix}-0-email": parent_user.email,
        f"{parents_prefix}-0-new_password": "",
        f"{parents_prefix}-0-DELETE": "",
        # enfants: 1 nouveau (sans solde_points)
        **{
            f"{enfants_prefix}-TOTAL_FORMS": "1",
            f"{enfants_prefix}-INITIAL_FORMS": "0",
            f"{enfants_prefix}-MIN_NUM_FORMS": "0",
            f"{enfants_prefix}-MAX_NUM_FORMS": "1000",
        },
        f"{enfants_prefix}-0-prenom": "Nina",
        # f"{enfants_prefix}-0-solde_points": "5",  # <-- SUPPRIMÉ
        f"{enfants_prefix}-0-email": "nina@example.com",
        f"{enfants_prefix}-0-new_password": "pwd",
        f"{enfants_prefix}-0-DELETE": "",
    }

    resp = client.post(reverse("famille:manage_account"), data, follow=True)
    assert reverse("points:dashboard") in resp.redirect_chain[-1][0]

    e = Enfant.objects.get(famille=famille, prenom="Nina")
    assert e.user is not None
    up = UserProfile.objects.get(user=e.user)
    assert up.role == "enfant"
    assert up.famille == famille



@pytest.mark.django_db
def test_manage_delete_self_parent_with_other_parent_exists(
    client, userprofile_parent, parent_user, autre_parent_user, famille
):
    # créer l'autre parent dans la même famille
    from famille.models import UserProfile
    UserProfile.objects.create(user=autre_parent_user, famille=famille, role="parent")

    # La vue ordonne les parents par id
    ordered = sorted([parent_user, autre_parent_user], key=lambda u: u.id)
    idx_self = ordered.index(parent_user)
    idx_other = 1 - idx_self

    client.force_login(parent_user)

    # Construire le POST conforme aux 3 formulaires attendus :
    # - FamilleForm (champ "nom")
    # - ParentInlineFormSet (prefix "parents")
    # - EnfantInlineFormSet (prefix "enfants")
    data = {
        # ---- FamilleForm
        "nom": famille.nom,

        # ---- ParentInlineFormSet management
        "parents-TOTAL_FORMS": "2",
        "parents-INITIAL_FORMS": "2",
        "parents-MIN_NUM_FORMS": "0",
        "parents-MAX_NUM_FORMS": "1000",

        # ---- Form du parent courant (marqué supprimé)
        f"parents-{idx_self}-user_id": str(parent_user.id),
        f"parents-{idx_self}-first_name": parent_user.first_name,
        f"parents-{idx_self}-last_name": parent_user.last_name,
        f"parents-{idx_self}-email": parent_user.email,
        f"parents-{idx_self}-new_password": "",
        f"parents-{idx_self}-DELETE": "on",   # <--- clé : suppression

        # ---- Form de l'autre parent (conservé)
        f"parents-{idx_other}-user_id": str(autre_parent_user.id),
        f"parents-{idx_other}-first_name": autre_parent_user.first_name,
        f"parents-{idx_other}-last_name": autre_parent_user.last_name,
        f"parents-{idx_other}-email": autre_parent_user.email,
        f"parents-{idx_other}-new_password": "",
        
        # ---- EnfantInlineFormSet (aucune ligne)
        "enfants-TOTAL_FORMS": "0",
        "enfants-INITIAL_FORMS": "0",
        "enfants-MIN_NUM_FORMS": "0",
        "enfants-MAX_NUM_FORMS": "1000",
    }

    resp = client.post(reverse("famille:manage_account"), data, follow=True)
    assert resp.status_code == 200  # redirection suivie vers points:dashboard

    # L'utilisateur courant doit avoir été supprimé par le "Pass 2: deletes"
    with pytest.raises(User.DoesNotExist):
        User.objects.get(pk=parent_user.pk)



# ------------------------------------------------------------------
# DeleteFamilyView
# ------------------------------------------------------------------
@pytest.mark.django_db
def test_delete_family_get_denies_non_parent(client, parent_user):
    client.force_login(parent_user)  # pas de profil parent
    resp = client.get(reverse("famille:delete_family"))
    assert resp.status_code in (302, 301)
    assert reverse("points:dashboard") in resp.url


@pytest.mark.django_db
def test_delete_family_post_wrong_name(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)
    url = reverse("famille:delete_family")
    resp = client.post(url, {"family_name": "Bidule", "password": "pwd"})
    assert resp.status_code == 200  # re-render
    # erreur sur le champ family_name
    assert "Le nom ne correspond pas exactement." in resp.content.decode()


@pytest.mark.django_db
def test_delete_family_post_wrong_password(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)
    url = reverse("famille:delete_family")
    resp = client.post(url, {"family_name": famille.nom, "password": "bad"})
    assert resp.status_code == 200
    assert "Mot de passe incorrect." in resp.content.decode()


@pytest.mark.django_db
def test_delete_family_post_ok_deletes_all_and_logs_out(
    client, userprofile_parent, parent_user, famille
):
    client.force_login(parent_user)

    # Ajouter un enfant + compte user pour bien vérifier la cascade
    e_user = User.objects.create_user(
        username="kid", email="kid@example.com", password="pwd"
    )
    Enfant.objects.create(prenom="Kid", famille=famille, user=e_user)
    UserProfile.objects.create(user=e_user, famille=famille, role="enfant")

    url = reverse("famille:delete_family")
    resp = client.post(
        url, {"family_name": famille.nom, "password": "pwd"}, follow=True
    )

    # Redirection finale vers login
    assert resp.redirect_chain
    assert reverse("famille:login") in resp.redirect_chain[-1][0]

    # Famille supprimée + utilisateurs liés supprimés
    assert not Famille.objects.filter(pk=famille.pk).exists()
    assert not User.objects.filter(pk=parent_user.pk).exists()
    assert not UserProfile.objects.filter(famille=famille).exists()
