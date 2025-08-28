from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View, ListView, TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
# from django.contrib.auth.decorators import permission_required as permission_required_decorator
from django.db.models import Sum
from .models import (
    BaremeRecompense,
    BaremePointPositif,
    BaremePointNegatif,
    PointNegatif,
    PointPositif,
)
from famille.models import Enfant
from famille.mixins import EnfantFamilleMixin, get_user_famille
from .forms import (
    PointsPositifsCreationForm,
    PointsNegatifsCreationForm,
    PointPositifFormSet,
    PointNegatifFormSet,
)


class HomeView(TemplateView):
    template_name = "points/home.html"



@login_required
def bareme_view(request):
    # (pré-remplissage si vide) — inchangé …

    can_edit = (
        request.user.is_staff
        or request.user.has_perm("points.change_baremerecompense")
        or request.user.has_perm("points.change_baremepointpositif")
        or request.user.has_perm("points.change_baremepointnegatif")
    )

    return render(
        request,
        "points/bareme.html",
        {
            "recompenses": BaremeRecompense.objects.all(),
            "positifs": BaremePointPositif.objects.all(),
            "negatifs": BaremePointNegatif.objects.all(),
            "can_edit": can_edit,
        },
    )


@login_required
def update_cell(request, model_name, pk, field):
    model_map = {
        "recompense": BaremeRecompense,
        "positif": BaremePointPositif,
        "negatif": BaremePointNegatif,
    }
    if model_name not in model_map:
        return HttpResponseBadRequest("Model inconnu")

    # 🔐 Vérif permission d’édition
    perm_map = {
        "recompense": "points.change_baremerecompense",
        "positif": "points.change_baremepointpositif",
        "negatif": "points.change_baremepointnegatif",
    }
    if not (request.user.is_staff or request.user.has_perm(perm_map[model_name])):
        return HttpResponseForbidden("Non autorisé")

    model = model_map[model_name]
    obj = get_object_or_404(model, pk=pk)

    ctx = {"model_name": model_name, "pk": obj.pk, "field": field}

    if request.method == "POST":
        value = request.POST.get("value", "")
        if field == "points":
            try:
                value = int(value)
            except ValueError:
                ctx["value"] = getattr(obj, field)
                return render(request, "points/cell_value.html", ctx)

        setattr(obj, field, value)
        obj.save()
        ctx["value"] = getattr(obj, field)
        return render(request, "points/cell_value.html", ctx)

    ctx["value"] = getattr(obj, field)
    return render(request, "points/cell_form.html", ctx)


# points/views.py
@login_required
@require_POST
def delete_row(request, model_name, pk):
    model_map = {
        "recompense": BaremeRecompense,
        "positif": BaremePointPositif,
        "negatif": BaremePointNegatif,
    }
    perm_map = {
        "recompense": "points.delete_baremerecompense",
        "positif": "points.delete_baremepointpositif",
        "negatif": "points.delete_baremepointnegatif",
    }

    if model_name not in model_map:
        return HttpResponseBadRequest("Model inconnu")
    if not (request.user.is_staff or request.user.has_perm(perm_map[model_name])):
        return HttpResponseForbidden("Non autorisé")

    model = model_map[model_name]
    obj = get_object_or_404(model, pk=pk)
    obj.delete()

    # <= 200 OK + chaîne vide : la <tr> ciblée est remplacée par rien => disparait
    return HttpResponse("")


@login_required
@require_POST
def add_row(request, model_name):
    model_map = {
        "recompense": BaremeRecompense,
        "positif": BaremePointPositif,
        "negatif": BaremePointNegatif,
    }
    add_perm_map = {
        "recompense": "points.add_baremerecompense",
        "positif": "points.add_baremepointpositif",
        "negatif": "points.add_baremepointnegatif",
    }
    if model_name not in model_map:
        return HttpResponseBadRequest("Model inconnu")

    if not (request.user.is_staff or request.user.has_perm(add_perm_map[model_name])):
        return HttpResponseForbidden("Non autorisé")

    # Valeurs par défaut (à adapter si tu veux)
    if model_name == "recompense":
        obj = BaremeRecompense.objects.create(points=0, valeur_euros="", valeur_temps="")
    elif model_name == "positif":
        obj = BaremePointPositif.objects.create(motif="(nouveau)", points=1)
    else:  # "negatif"
        obj = BaremePointNegatif.objects.create(motif="(nouveau)", points=-1)

    # Même logique que dans bareme_view pour l’édition
    can_edit = (
        request.user.is_staff
        or request.user.has_perm("points.change_baremerecompense")
        or request.user.has_perm("points.change_baremepointpositif")
        or request.user.has_perm("points.change_baremepointnegatif")
    )

    return render(
        request,
        "points/row.html",
        {"model_name": model_name, "obj": obj, "can_edit": can_edit},
    )


class DashboardView(
    LoginRequiredMixin, PermissionRequiredMixin, EnfantFamilleMixin, ListView
):
    """
    Liste uniquement les enfants de MA famille
    grâce à EnfantFamilleMixin.get_queryset().
    """

    template_name = "points/index.html"
    context_object_name = "enfants_list"
    model = Enfant  # super().get_queryset() => Enfant.objects.all(), puis filtré par le mixin
    permission_required = (
        "points.view_pointpositif",
        "points.view_pointnegatif",
    )


class NewPointsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Création de nouveaux points pour un enfant donné (pk).
    On vérifie explicitement que l'enfant appartient bien à MA famille.
    """

    form_classes = [PointsPositifsCreationForm, PointsNegatifsCreationForm]
    template_name = "points/new_points.html"
    success_url = "points:dashboard"
    permission_required = (
        "famille.view_enfant",
        "points.add_pointpositif",
        "points.add_pointnegatif",
    )

    def _get_enfant_owned(self, request, pk):
        """Récupère l'enfant et vérifie l'appartenance à la famille de l'utilisateur."""
        enfant = get_object_or_404(Enfant, pk=pk)
        # Superuser : accès total
        if request.user.is_superuser:
            return enfant
        famille = get_user_famille(request)
        if not famille or enfant.famille_id != famille.id:
            raise PermissionDenied(
                "Cet enfant n'appartient pas à votre famille."
            )
        return enfant

    def get(self, request, pk):
        """Répond aux requêtes GET."""
        enfant = self._get_enfant_owned(request, pk)
        forms = [form() for form in self.form_classes]
        return render(
            request,
            self.template_name,
            {"forms": forms, "enfant": enfant},
        )

    def post(self, request, pk):
        """Répond aux requêtes POST."""
        enfant = self._get_enfant_owned(request, pk)
        forms = [form(request.POST) for form in self.form_classes]

        if all(form.is_valid() for form in forms):
            point_positif_form, point_negatif_form = forms

            point_positif = point_positif_form.save(commit=False)
            point_positif.enfant_id = enfant.id

            point_negatif = point_negatif_form.save(commit=False)
            point_negatif.enfant_id = enfant.id

            # Enregistre seulement s'il y a un nombre > 0
            saved_any = False
            if getattr(point_positif, "nb_positif", 0) > 0:
                point_positif.save()
                saved_any = True
            if getattr(point_negatif, "nb_negatif", 0) > 0:
                point_negatif.save()
                saved_any = True

            # Mets à jour le solde une seule fois (delta)
            delta = getattr(point_positif, "nb_positif", 0) - getattr(
                point_negatif, "nb_negatif", 0
            )
            if delta != 0:
                enfant.solde_points = (enfant.solde_points or 0) + delta
                enfant.save(update_fields=["solde_points"])

            if saved_any:
                messages.success(
                    request, "Les points ont bien été enregistrés."
                )
            else:
                messages.info(
                    request, "Aucun point n’a été ajouté (valeurs à 0)."
                )

            return redirect(self.success_url)

        # Formulaires invalides
        return render(
            request,
            self.template_name,
            {"forms": forms, "enfant": enfant},
        )


new_points_view = NewPointsView.as_view()


@login_required
def historique_editable(request, pk):
    """
    Vue pour éditer l'historique des points d'un enfant.
    @permission_required n'est pas utilisé sinon les enfants seraient bloqués dès l’accès. La sécurité est assurée par :
    -le filtrage famille=request.user.profile.famille
    -le POST interdit si not is_parent.
    """
    enfant = get_object_or_404(Enfant, pk=pk, famille=request.user.profile.famille)

    qs_pos = PointPositif.objects.filter(enfant=enfant).order_by("-date", "-id")
    qs_neg = PointNegatif.objects.filter(enfant=enfant).order_by("-date", "-id")

    # Parent = a les deux permissions de modification
    is_parent = (
        request.user.has_perm("points.change_pointpositif")
        and request.user.has_perm("points.change_pointnegatif")
    )

    if request.method == "POST":
        if not is_parent:
            return HttpResponseForbidden("Accès réservé aux parents.")
        pos_fs = PointPositifFormSet(request.POST, prefix="pp", queryset=qs_pos)
        neg_fs = PointNegatifFormSet(request.POST, prefix="pn", queryset=qs_neg)
        if pos_fs.is_valid() and neg_fs.is_valid():
            pos_fs.save()
            neg_fs.save()

            # Recalcul du solde
            total_pos = (
                PointPositif.objects.filter(enfant=enfant).aggregate(total=Sum("nb_positif"))["total"] or 0
            )
            total_neg = (
                PointNegatif.objects.filter(enfant=enfant).aggregate(total=Sum("nb_negatif"))["total"] or 0
            )
            enfant.solde_points = total_pos - total_neg
            enfant.save(update_fields=["solde_points"])

            messages.success(request, "Modifications enregistrées ✅")
            return redirect("points:historique", pk=enfant.id)
        else:
            print("errors POS:", pos_fs.errors)
            print("errors NEG:", neg_fs.errors)
    else:
        pos_fs = PointPositifFormSet(prefix="pp", queryset=qs_pos)
        neg_fs = PointNegatifFormSet(prefix="pn", queryset=qs_neg)

    return render(
        request,
        "points/historique.html",
        {
            "enfant": enfant,
            "pos_fs": pos_fs,
            "neg_fs": neg_fs,
            "is_parent": is_parent,
        },
    )
