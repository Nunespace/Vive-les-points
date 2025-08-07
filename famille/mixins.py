import logging
from django.core.exceptions import PermissionDenied
from django.db.models import (
    ForeignKey,
)  # Importé pour vérifier si un champ est une clé étrangère (FK) vers un autre modèle.
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.edit import CreateView

logger = logging.getLogger(__name__)


class FamilleMixin:
    """
    Filtre les objets d'une vue pour n'afficher que ceux de la famille de l'utilisateur connecté (à condition que le
    modèle ait une FK vers Famille) et associe la famille lors de la validation d'un formulaire si le modèle dispose
    d'un champ famille.
    """

    def get_famille(self):
        """
        Récupère la famille de l'utilisateur connecté s'il est associé à une famille.
        """
        if hasattr(self.request.user, "profile") and self.request.user.profile.famille:
            return self.request.user.profile.famille
        return None

    def get_queryset(self):
        """
        Filtre les objets pour n'afficher que ceux de la famille de l'utilisateur connecté à condition que le modèle
        ait une FK vers Famille. Fonctionne avec les vues génériques :
        - ListView
        - DetailView
        - UpdateView
        - DeleteView
        """
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        return qs.filter(famille=user.profile.famille)

    def form_valid(self, form):
        """
        Associe la famille de l'utilisateur connecté au modèle pour les views génériques dotées de la méthode form_valid
        """
        # On récupère l'utilisateur connecté
        user = self.request.user
        if user and hasattr(user, "profile"):
            # Associe la famille de l'utilisateur au modèle
            form.instance.famille = user.profile.famille
        return super().form_valid(form)