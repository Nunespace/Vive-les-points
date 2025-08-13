from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import View, ListView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Importe Enfant depuis l'app famille (cohérent avec les mixins)
from famille.models import Enfant
from famille.mixins import EnfantFamilleMixin, get_user_famille

# Les modèles de points restent dans l'app points
from .models import Point_negatif, Point_positif
from .forms import (
    PointsPositifsCreationForm,
    PointsNegatifsCreationForm,
)


def bareme(request):
    """Vue gérant l'affichage du barème."""
    return render(request, "points/bareme.html")


class IndexView(LoginRequiredMixin, PermissionRequiredMixin, EnfantFamilleMixin, ListView):
    """
    Liste uniquement les enfants de MA famille
    grâce à EnfantFamilleMixin.get_queryset().
    """
    template_name = "points/index.html"
    context_object_name = "enfants_list"
    model = Enfant  # super().get_queryset() => Enfant.objects.all(), puis filtré par le mixin
    permission_required = ("points.view_point_positif", "points.view_point_negatif")


class DetailView(LoginRequiredMixin, PermissionRequiredMixin, EnfantFamilleMixin, DetailView):
    """
    Détail d’un enfant de sa famille (historique).
    L’accès est bloqué si l’enfant n’appartient pas à l’utilisateur.
    """
    model = Enfant
    template_name = "points/historique.html"
    context_object_name = "enfant"
    permission_required = ("famille.view_enfant", "points.view_point_positif", "points.view_point_negatif")


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
        "points.add_point_positif",
        "points.add_point_negatif",
    )

    def _get_enfant_owned(self, request, pk):
        """Récupère l'enfant et vérifie l'appartenance à la famille de l'utilisateur."""
        enfant = get_object_or_404(Enfant, pk=pk)
        # Superuser : accès total
        if request.user.is_superuser:
            return enfant
        famille = get_user_famille(request)
        if not famille or enfant.famille_id != famille.id:
            raise PermissionDenied("Cet enfant n'appartient pas à votre famille.")
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
            delta = getattr(point_positif, "nb_positif", 0) - getattr(point_negatif, "nb_negatif", 0)
            if delta != 0:
                enfant.solde_points = (enfant.solde_points or 0) + delta
                enfant.save(update_fields=["solde_points"])

            if saved_any:
                messages.success(request, "Les points ont bien été enregistrés.")
            else:
                messages.info(request, "Aucun point n’a été ajouté (valeurs à 0).")

            return redirect(self.success_url)

        # Formulaires invalides
        return render(
            request,
            self.template_name,
            {"forms": forms, "enfant": enfant},
        )


new_points_view = NewPointsView.as_view()
