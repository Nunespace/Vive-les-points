import pytest
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse

from points.models import (
    BaremeRecompense,
    BaremePointPositif,
    BaremePointNegatif,
    PointPositif,
    PointNegatif,
)

ISO = "%Y-%m-%d"


# -------------------------------------------------------------------
# bareme_view
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_bareme_view_requires_login(client):
    resp = client.get(reverse("points:bareme"))
    # redirection non authentifié (302 vers login)
    assert resp.status_code in (301, 302)


@pytest.mark.django_db
def test_bareme_view_context_and_can_edit_flag(client, userprofile_parent, parent_user):
    # données
    BaremeRecompense.objects.create(points=10, valeur_euros="5€", valeur_temps="30min")
    BaremePointPositif.objects.create(motif="Devoirs", points=1)
    BaremePointNegatif.objects.create(motif="Bêtise", points=-1)

    # utilisateur non staff sans perms => can_edit False
    client.force_login(parent_user)
    resp = client.get(reverse("points:bareme"))
    assert resp.status_code == 200
    assert "recompenses" in resp.context
    assert "positifs" in resp.context
    assert "negatifs" in resp.context
    assert resp.context["can_edit"] is False

    # utilisateur staff => can_edit True
    parent_user.is_staff = True
    parent_user.save()
    resp2 = client.get(reverse("points:bareme"))
    assert resp2.status_code == 200
    assert resp2.context["can_edit"] is True


# -------------------------------------------------------------------
# update_cell
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_update_cell_forbidden_without_perm(client, userprofile_parent, parent_user):
    obj = BaremePointPositif.objects.create(motif="X", points=1)
    client.force_login(parent_user)
    url = reverse("points:update_cell", args=["positif", obj.pk, "points"])
    resp = client.get(url)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_update_cell_get_and_post_update_with_perm(client, userprofile_parent, parent_user, give_perms):
    obj = BaremePointPositif.objects.create(motif="X", points=1)
    give_perms(parent_user, ["points.change_baremepointpositif"])
    client.force_login(parent_user)

    # GET => form
    url = reverse("points:update_cell", args=["positif", obj.pk, "points"])
    r_get = client.get(url)
    assert r_get.status_code == 200
    # POST => maj valeur
    r_post = client.post(url, {"value": "5"})
    assert r_post.status_code == 200
    obj.refresh_from_db()
    assert obj.points == 5


@pytest.mark.django_db
def test_update_cell_post_invalid_int_keeps_value(client, userprofile_parent, parent_user, give_perms):
    obj = BaremePointPositif.objects.create(motif="X", points=7)
    give_perms(parent_user, ["points.change_baremepointpositif"])
    client.force_login(parent_user)
    url = reverse("points:update_cell", args=["positif", obj.pk, "points"])
    r = client.post(url, {"value": "abc"})
    assert r.status_code == 200
    obj.refresh_from_db()
    assert obj.points == 7  # inchangé


@pytest.mark.django_db
def test_update_cell_bad_model_name_returns_400(client, userprofile_parent, parent_user):
    client.force_login(parent_user)
    url = reverse("points:update_cell", args=["inconnu", 1, "points"])
    r = client.get(url)
    assert r.status_code == 400


# -------------------------------------------------------------------
# delete_row
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_delete_row_requires_post(client, userprofile_parent, parent_user):
    obj = BaremePointNegatif.objects.create(motif="Y", points=-1)
    client.force_login(parent_user)
    url = reverse("points:delete_row", args=["negatif", obj.pk])
    r = client.get(url)
    assert r.status_code == 405  # require_POST


@pytest.mark.django_db
def test_delete_row_forbidden_without_perm(client, userprofile_parent, parent_user):
    obj = BaremePointNegatif.objects.create(motif="Y", points=-1)
    client.force_login(parent_user)
    url = reverse("points:delete_row", args=["negatif", obj.pk])
    r = client.post(url)
    assert r.status_code == 403


@pytest.mark.django_db
def test_delete_row_with_perm_deletes_and_returns_empty(client, userprofile_parent, parent_user, give_perms):
    obj = BaremePointNegatif.objects.create(motif="Y", points=-1)
    give_perms(parent_user, ["points.delete_baremepointnegatif"])
    client.force_login(parent_user)
    url = reverse("points:delete_row", args=["negatif", obj.pk])
    r = client.post(url)
    assert r.status_code == 200
    assert r.content == b""
    assert not BaremePointNegatif.objects.filter(pk=obj.pk).exists()


# -------------------------------------------------------------------
# add_row
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_add_row_forbidden_without_perm(client, userprofile_parent, parent_user):
    client.force_login(parent_user)
    url = reverse("points:add_row", args=["positif"])
    r = client.post(url)
    assert r.status_code == 403


@pytest.mark.django_db
def test_add_row_creates_positif_with_perm(client, userprofile_parent, parent_user, give_perms):
    give_perms(parent_user, ["points.add_baremepointpositif"])
    client.force_login(parent_user)
    url = reverse("points:add_row", args=["positif"])
    r = client.post(url)
    assert r.status_code == 200
    obj = BaremePointPositif.objects.latest("id")
    assert obj.motif == "(nouveau)"
    assert obj.points == 1


@pytest.mark.django_db
def test_add_row_creates_recompense_with_perm(client, userprofile_parent, parent_user, give_perms):
    give_perms(parent_user, ["points.add_baremerecompense"])
    client.force_login(parent_user)
    url = reverse("points:add_row", args=["recompense"])
    r = client.post(url)
    assert r.status_code == 200
    obj = BaremeRecompense.objects.latest("id")
    assert obj.points == 0
    assert obj.valeur_euros == ""
    assert obj.valeur_temps == ""


@pytest.mark.django_db
def test_add_row_creates_negatif_with_perm(client, userprofile_parent, parent_user, give_perms):
    give_perms(parent_user, ["points.add_baremepointnegatif"])
    client.force_login(parent_user)
    url = reverse("points:add_row", args=["negatif"])
    r = client.post(url)
    assert r.status_code == 200
    obj = BaremePointNegatif.objects.latest("id")
    assert obj.motif == "(nouveau)"
    assert obj.points == -1


@pytest.mark.django_db
def test_add_row_bad_model_name_400(client, userprofile_parent, parent_user):
    client.force_login(parent_user)
    url = reverse("points:add_row", args=["inconnu"])
    r = client.post(url)
    assert r.status_code == 400


# -------------------------------------------------------------------
# DashboardView
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_dashboard_lists_only_children_of_my_family(client, userprofile_parent, parent_user, famille, autre_famille, give_perms):
    # Enfants multi-familles
    mine = Enfant.objects.create(prenom="Léa", famille=famille)
    other = Enfant.objects.create(prenom="Tom", famille=autre_famille)

    # Permissions requises par la vue
    give_perms(parent_user, ["points.view_pointpositif", "points.view_pointnegatif"])
    client.force_login(parent_user)

    resp = client.get(reverse("points:dashboard"))
    assert resp.status_code == 200
    enfants = list(resp.context["enfants_list"])
    assert mine in enfants
    assert other not in enfants


# -------------------------------------------------------------------
# NewPointsView
# -------------------------------------------------------------------
from famille.models import Enfant

@pytest.mark.django_db
def test_new_points_get_ok_for_my_child(client, userprofile_parent, parent_user, famille, give_perms):
    child = Enfant.objects.create(prenom="Léa", famille=famille)
    give_perms(parent_user, ["famille.view_enfant", "points.add_pointpositif", "points.add_pointnegatif"])
    client.force_login(parent_user)

    r = client.get(reverse("points:new_points", args=[child.pk]))
    assert r.status_code == 200
    assert "forms" in r.context
    assert "enfant" in r.context
    assert r.context["enfant"].pk == child.pk


@pytest.mark.django_db
def test_new_points_forbidden_on_foreign_child(client, userprofile_parent, parent_user, autre_famille, give_perms):
    # enfant d'une autre famille
    foreign = Enfant.objects.create(prenom="Tom", famille=autre_famille)
    give_perms(parent_user, ["famille.view_enfant", "points.add_pointpositif", "points.add_pointnegatif"])
    client.force_login(parent_user)

    r = client.get(reverse("points:new_points", args=[foreign.pk]))
    assert r.status_code == 403  # PermissionDenied


@pytest.mark.django_db
def test_new_points_post_saves_and_updates_solde(client, userprofile_parent, parent_user, famille, give_perms):
    child = Enfant.objects.create(prenom="Léa", famille=famille, solde_points=0)
    give_perms(parent_user, ["famille.view_enfant", "points.add_pointpositif", "points.add_pointnegatif"])
    client.force_login(parent_user)

    url = reverse("points:new_points", args=[child.pk])
    data = {
        # form 1: positifs
        "nb_positif": "3",
        "motif1": "OK",
        # form 2: négatifs
        "nb_negatif": "1",
        "motif2": "KO",
    }
    r = client.post(url, data, follow=True)
    assert r.redirect_chain  # redirige vers dashboard
    child.refresh_from_db()
    assert child.solde_points == 2  # 3 - 1


@pytest.mark.django_db
def test_new_points_post_all_zero_infos_message(client, userprofile_parent, parent_user, famille, give_perms):
    child = Enfant.objects.create(prenom="Zoé", famille=famille, solde_points=5)
    give_perms(parent_user, ["famille.view_enfant", "points.add_pointpositif", "points.add_pointnegatif"])
    client.force_login(parent_user)

    url = reverse("points:new_points", args=[child.pk])
    data = {"nb_positif": "0", "motif1": "", "nb_negatif": "0", "motif2": ""}
    r = client.post(url, data, follow=True)
    assert r.redirect_chain
    child.refresh_from_db()
    assert child.solde_points == 5  # inchangé


# -------------------------------------------------------------------
# historique_editable
# -------------------------------------------------------------------
@pytest.mark.django_db
def test_historique_get_ok_and_flag_is_parent_false_when_no_change_perms(
    client, userprofile_parent, parent_user, enfant
):
    client.force_login(parent_user)
    r = client.get(reverse("points:historique", args=[enfant.pk]))
    assert r.status_code == 200
    assert r.context["is_parent"] is False


@pytest.mark.django_db
def test_historique_post_forbidden_if_not_parent(client, userprofile_parent, parent_user, enfant):
    client.force_login(parent_user)
    r = client.post(reverse("points:historique", args=[enfant.pk]))
    assert r.status_code == 403
    assert "Accès réservé aux parents." in r.content.decode("utf-8")



@pytest.mark.django_db
def test_historique_post_updates_totals_and_solde(
    client, userprofile_parent, parent_user, enfant, give_perms
):
    # Données initiales
    p = PointPositif.objects.create(enfant=enfant, nb_positif=1, motif1="A", date=timezone.localdate())
    n = PointNegatif.objects.create(enfant=enfant, nb_negatif=1, motif2="B", date=timezone.localdate())
    enfant.solde_points = 0
    enfant.save()

    # Donne les perms de modification => "parent" au sens de la vue
    give_perms(parent_user, ["points.change_pointpositif", "points.change_pointnegatif"])
    client.force_login(parent_user)

    url = reverse("points:historique", args=[enfant.pk])

    data = {
        # Formset POSITIF (prefix pp), 1 form initial
        "pp-TOTAL_FORMS": "1",
        "pp-INITIAL_FORMS": "1",
        "pp-MIN_NUM_FORMS": "0",
        "pp-MAX_NUM_FORMS": "1000",
        "pp-0-id": str(p.id),
        "pp-0-date": timezone.localdate().strftime(ISO),
        "pp-0-nb_positif": "5",
        "pp-0-motif1": "A+",
        "pp-0-DELETE": "",

        # Formset NEGATIF (prefix pn), 1 form initial
        "pn-TOTAL_FORMS": "1",
        "pn-INITIAL_FORMS": "1",
        "pn-MIN_NUM_FORMS": "0",
        "pn-MAX_NUM_FORMS": "1000",
        "pn-0-id": str(n.id),
        "pn-0-date": timezone.localdate().strftime(ISO),
        "pn-0-nb_negatif": "2",
        "pn-0-motif2": "B-",
        "pn-0-DELETE": "",
    }

    r = client.post(url, data, follow=True)
    assert r.redirect_chain
    enfant.refresh_from_db()
    # total_pos = 5, total_neg = 2 => solde = 3
    assert enfant.solde_points == 3
