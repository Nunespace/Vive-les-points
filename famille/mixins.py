# famille/mixins.py
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import CreateView
from famille.models import Enfant


# --- Utils ---
# --- Utils ---
def get_user_famille(request):
    """
    Récupère l'objet Famille associé à l'utilisateur courant.
    Essaie d'abord via le profil parent (UserProfile : user.profile.famille),
    puis via le profil enfant (Enfant : user.profil_enfant.famille).
    Retourne None si aucune famille n'est trouvée.
    """

    # Récupère l'attribut "user" depuis l'objet request
    # - Si "user" existe → renvoyé dans u
    # - Sinon → valeur par défaut = None
    u = getattr(request, "user", None)

    # Si aucun utilisateur ou si l'utilisateur n'est pas connecté (anonyme),
    # on arrête immédiatement : il n'a pas de famille à retourner.
    if not u or not u.is_authenticated:
        return None

    # 1) Tentative de récupération via le profil "parent"
    # - On vérifie que l'objet utilisateur a bien un attribut "profile"
    # - On s'assure que ce profil est défini (non None)
    # - On vérifie que la famille associée a un ID valide
    try:
        if hasattr(u, "profile") and u.profile and u.profile.famille_id is not None:
            return u.profile.famille
    except Exception:
        # En cas d'erreur (profil absent, accès impossible, etc.), on ignore
        pass

    # 2) Tentative de récupération via le profil "enfant"
    # - Même logique que pour le profil parent
    try:
        if hasattr(u, "profil_enfant") and u.profil_enfant and u.profil_enfant.famille_id is not None:
            return u.profil_enfant.famille
    except Exception:
        # Idem : on ignore les erreurs éventuelles
        pass

    # Si aucun des deux cas n'a fonctionné, on retourne None
    return None




# ============= 1) ENFANT: accès limité à MA famille =============
class EnfantFamilleMixin:
    """
    Restreint l'accès aux Enfant appartenant à la famille de l'utilisateur.
    - get_queryset(): Enfant.objects.filter(famille=ma_famille)
    - dispatch(): vérifie que l'objet (Detail/Update/Delete) appartient bien à ma famille
    - form_valid(): impose instance.famille = ma_famille à la création/modif
    """

    famille_field_name = "famille"  # Sur le modèle Enfant

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        famille = get_user_famille(request)
        if not famille:
            raise PermissionDenied("Vous n'êtes pas associé à une famille.")

        # Vérif objet pour Detail/Update/Delete (pas pour Create)
        if hasattr(self, "get_object") and not isinstance(self, CreateView):
            obj = self.get_object()
            if getattr(obj, f"{self.famille_field_name}_id", None) != famille.id:
                raise PermissionDenied("Cet enfant n'appartient pas à votre famille.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        famille = get_user_famille(self.request)
        return qs.filter(**{self.famille_field_name: famille}) if famille else qs.none()

    def form_valid(self, form):
        if self.request.user.is_superuser:
            return super().form_valid(form)
        famille = get_user_famille(self.request)
        if not famille:
            raise PermissionDenied("Vous n'êtes pas associé à une famille.")
        # Force l'appartenance
        setattr(form.instance, self.famille_field_name, famille)
        return super().form_valid(form)


# ============= 2) POINTS: accès limité aux ENFANTS de MA famille =============
class PointsFamilleMixin:
    """
    Restreint l'accès aux points (positifs/négatifs) rattachés à un Enfant de MA famille.
    Hypothèse: le modèle a un FK 'enfant' vers Enfant.
    - get_queryset(): filter(enfant__famille=ma_famille)
    - get_form(): limite le champ 'enfant' aux enfants de ma famille
    - dispatch(): vérifie que obj.enfant.famille == ma_famille (Detail/Update/Delete)
    - form_valid(): refuse si l'enfant choisi n'est pas de ma famille
    """

    enfant_field_name = "enfant"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        famille = get_user_famille(request)
        if not famille:
            raise PermissionDenied("Vous n'êtes pas associé à une famille.")

        if hasattr(self, "get_object") and not isinstance(self, CreateView):
            obj = self.get_object()
            enfant = getattr(obj, self.enfant_field_name, None)
            if not enfant or enfant.famille_id != famille.id:
                raise PermissionDenied("Cet objet est lié à un enfant d'une autre famille.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        famille = get_user_famille(self.request)
        return qs.filter(**{f"{self.enfant_field_name}__famille": famille}) if famille else qs.none()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.is_superuser:
            return form
        # Restreindre le choix d'enfants
        if self.enfant_field_name in form.fields:
            famille = get_user_famille(self.request)
            form.fields[self.enfant_field_name].queryset = (
                Enfant.objects.filter(famille=famille) if famille else Enfant.objects.none()
            )
        return form

    def form_valid(self, form):
        if self.request.user.is_superuser:
            return super().form_valid(form)
        famille = get_user_famille(self.request)
        if not famille:
            raise PermissionDenied("Vous n'êtes pas associé à une famille.")

        enfant = getattr(form.instance, self.enfant_field_name, None)
        if not enfant or enfant.famille_id != famille.id:
            raise PermissionDenied("Cet enfant n'appartient pas à votre famille.")
        return super().form_valid(form)
