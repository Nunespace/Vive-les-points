from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import View, ListView, DetailView
from .models import Enfant, Point_negatif, Point_positif
from .forms import (
    PointsPositifsCreationForm,
    PointsNegatifsCreationForm,
)

from django.contrib import messages


def bareme(request):
    """Vue gérant l'affichage du barème."""
    return render(request, "points/bareme.html")


class IndexView(ListView):
    template_name = "points/index.html"
    context_object_name = "enfants_list"

    def get_queryset(self):
        """Retourne tous les enfants."""
        return Enfant.objects.all()


class DetailView(DetailView):
    model = Enfant
    template_name = "points/historique.html"


class NewPointsView(View):
    """Vue gérant l'affichage des nouveaux points."""

    form_classes = [PointsPositifsCreationForm, PointsNegatifsCreationForm]
    template_name = "points/new_points.html"
    success_url = "accueil"

    def get(self, request, pk):
        """Réponds aux requêtes GET."""
        forms = [form() for form in self.form_classes]
        enfant = get_object_or_404(Enfant, pk=pk)
        return render(
            request,
            self.template_name,
            {"forms": forms, "enfant": enfant},
        )

    def post(self, request, pk):
        """Réponds aux requêtes POST."""
        forms = [form(request.POST) for form in self.form_classes]
        enfant = get_object_or_404(Enfant, pk=pk)
        if all(form.is_valid() for form in forms):
            # Tous les formulaires sont valides
            point_positif_form, point_negatif_form = forms
            point_positif = point_positif_form.save(commit=False)
            point_positif.enfant_id = enfant.id
            point_negatif = point_negatif_form.save(commit=False)
            point_negatif.enfant_id = enfant.id
            if point_positif.nb_positif > 0:
                point_positif.save()
            if point_negatif.nb_negatif > 0:
                point_negatif.save()
            enfant.solde_points += point_positif.nb_positif
            enfant.save()
            enfant.solde_points -= point_negatif.nb_negatif
            enfant.save()
            return redirect(self.success_url)
        return render(
            request,
            self.template_name,
            {"forms": forms, "enfant": enfant},
        )


new_points_view = NewPointsView.as_view()
