# famille/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
import logging
log = logging.getLogger(__name__)

from .forms import (
    EmailAuthenticationForm,
    FamilleForm,
    ParentFormSet,
    EnfantSignupFormSet,   # <-- inscription (avec email/password enfants)
    ParentInlineFormSet,
    EnfantInlineFormSet,   # <-- gestion de compte (form modèle + champs extra)
    FamilyHardDeleteForm,
)
from .models import Famille, Enfant, UserProfile

User = get_user_model()
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views import View

from .models import UserProfile
from .forms import FamilleForm, ParentInlineFormSet, EnfantInlineFormSet

logger = logging.getLogger(__name__)


# ---------- Utils ----------
def _get_group(name: str) -> Group:
    """Récupère ou crée un groupe par nom ('parents', 'enfant')."""
    g, _ = Group.objects.get_or_create(name=name)
    return g


# ===================================================================
# ======================   AUTH (email)   ============================
# ===================================================================

class EmailLoginView(LoginView):
    template_name = "famille/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)  # 30 jours
        else:
            self.request.session.set_expiry(0)
        messages.success(self.request, "Connexion réussie.")
        return response

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("points:dashboard")


email_login_view = EmailLoginView.as_view()


class EmailLogoutView(LogoutView):
    next_page = reverse_lazy("famille:login")


email_logout_view = EmailLogoutView.as_view()


# ===================================================================
# ===================   INSCRIPTION FAMILLE   =======================
# ===================================================================

class RegisterFamilyView(View):
    """
    Crée :
      - Famille
      - Parents (Users + UserProfile + groupe 'parents')
      - Enfants (modèle) + éventuellement compte User enfant lié (OneToOne) + UserProfile + groupe 'enfant'
    Connecte automatiquement le 1er parent créé.
    """
    template_name = "famille/register.html"

    def get(self, request):
        ctx = {
            "famille_form": FamilleForm(),
            "parent_formset": ParentFormSet(prefix="parents"),
            "enfant_formset": EnfantSignupFormSet(prefix="enfants"),
        }
        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request):
        famille_form = FamilleForm(request.POST)
        parent_formset = ParentFormSet(request.POST, prefix="parents")
        enfant_formset = EnfantSignupFormSet(request.POST, prefix="enfants")

        if not (famille_form.is_valid() and parent_formset.is_valid() and enfant_formset.is_valid()):
            # Affichage d’un message d’erreurs agrégé
            from django.utils.html import format_html, format_html_join
            error_messages = []

            for field, errors in famille_form.errors.items():
                for err in errors:
                    error_messages.append(f"Famille – {field} : {err}")

            for i, form in enumerate(parent_formset.forms, start=1):
                for field, errors in form.errors.items():
                    for err in errors:
                        error_messages.append(f"Parent {i} – {field} : {err}")

            for i, form in enumerate(enfant_formset.forms, start=1):
                for field, errors in form.errors.items():
                    for err in errors:
                        error_messages.append(f"Enfant {i} – {field} : {err}")

            if error_messages:
                messages.error(
                    request,
                    format_html(
                        'Certains champs sont invalides :<ul class="mb-0">{}</ul>',
                        format_html_join('', '<li>{}</li>', ((e,) for e in error_messages))
                    )
                )
            return render(request, self.template_name, {
                "famille_form": famille_form,
                "parent_formset": parent_formset,
                "enfant_formset": enfant_formset,
            })

        # 1) Famille
        famille = famille_form.save()

        # 2) Parents
        parents_group = _get_group("parents")
        enfants_group = _get_group("enfant")

        first_parent = None
        for form in parent_formset:
            if form.cleaned_data.get("DELETE"):
                continue
            cd = form.cleaned_data
            user = User.objects.create_user(
                username=cd["email"],  # email comme identifiant
                email=cd["email"],
                password=cd["password1"],
                first_name=cd["first_name"],
                last_name=cd["last_name"],
            )
            user.groups.add(parents_group)
            UserProfile.objects.create(user=user, famille=famille, role="parent")
            if first_parent is None:
                first_parent = user

        # 3) Enfants (modèle) + (facultatif) compte User enfant lié (OneToOne)
        for form in enfant_formset:
            if form.cleaned_data.get("DELETE"):
                continue
            cd = form.cleaned_data

            enfant_obj = Enfant.objects.create(
                prenom=cd["prenom"],
                solde_points=cd.get("solde_points") or 0,
                famille=famille,
            )

            # créer un compte enfant si email fourni
            if cd.get("email"):
                u = User.objects.create_user(
                    username=cd["email"],
                    email=cd["email"],
                    password=cd["password"],
                    first_name=cd["prenom"],
                    last_name=famille.nom,
                )
                u.groups.add(enfants_group)
                UserProfile.objects.create(user=u, famille=famille, role="enfant")

                # Lier OneToOne
                enfant_obj.user = u
                enfant_obj.save(update_fields=["user"])

        messages.success(request, "Famille et utilisateurs créés avec succès.")

        # 4) Connexion du 1er parent
        if first_parent:
            # Pose explicitement le backend si nécessaire
            backend = getattr(settings, "AUTHENTICATION_BACKENDS", ["django.contrib.auth.backends.ModelBackend"])[0]
            login(request, first_parent, backend=backend)

        return redirect("points:dashboard")


register_family_view = RegisterFamilyView.as_view()


# ===================================================================
# ==============   GESTION DU COMPTE FAMILLE   ======================
# ===================================================================




class ManageFamilyAccountView(LoginRequiredMixin, View):
    """
    - Accès réservé aux users avec UserProfile(role='parent')
    - Edition du nom de famille
    - CRUD Parents (Users + UserProfile + groupe 'parents')
    - CRUD Enfants (modèle) + gestion du compte User enfant lié (email/mot de passe + UserProfile + groupe 'enfant')
    - Détection 'aucun changement'
    - Préserve la session si le parent connecté change son mdp
    """
    template_name = "famille/account_manage.html"

    # ---------- Utils accès ----------
    def _require_parent(self, request):
        try:
            return request.user.profile
        except UserProfile.DoesNotExist:
            return None

    def _ensure_parent_access(self, request):
        p = self._require_parent(request)
        return bool(p and p.role == "parent")

    def _parents_queryset(self, famille):
        return User.objects.filter(profile__famille=famille, profile__role="parent").order_by("id")

    # ---------- GET ----------
    def get(self, request):
        if not self._ensure_parent_access(request):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")

        logger.warning(f"[ACCOUNT][GET] start: auth={request.user.is_authenticated} "
                       f"session_key={getattr(request.session, 'session_key', None)}")

        famille = request.user.profile.famille

        famille_form = FamilleForm(instance=famille)

        parents = self._parents_queryset(famille)
        parent_initial = [{
            "user_id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "DELETE": False,
        } for u in parents]
        parent_formset = ParentInlineFormSet(initial=parent_initial, prefix="parents")

        enfant_formset = EnfantInlineFormSet(instance=famille, prefix="enfants")

        return render(request, self.template_name, {
            "famille_form": famille_form,
            "parent_formset": parent_formset,
            "enfant_formset": enfant_formset,
        })

    # ---------- POST ----------
    @transaction.atomic
    def post(self, request):
        # mémorise l'utilisateur courant
        current_user = request.user
        if not self._ensure_parent_access(request):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")

        famille = request.user.profile.famille

        logger.warning(f"[ACCOUNT][POST] start: auth={request.user.is_authenticated} "
                       f"session_key={getattr(request.session, 'session_key', None)}")

        if "delete_self" in request.POST:
            return self._delete_self_parent(request, famille)

        famille_form = FamilleForm(request.POST, instance=famille)
        parent_formset = ParentInlineFormSet(request.POST, prefix="parents")
        enfant_formset = EnfantInlineFormSet(request.POST, instance=famille, prefix="enfants")

        for form in parent_formset:
            form.famille = famille

        if not (famille_form.is_valid() and parent_formset.is_valid() and enfant_formset.is_valid()):
            logger.warning(f"[ACCOUNT][POST] invalid form(s): auth={request.user.is_authenticated} "
                           f"session_key={getattr(request.session, 'session_key', None)}")
            messages.error(request, "Merci de corriger les erreurs dans le formulaire.")
            return render(request, self.template_name, {
                "famille_form": famille_form,
                "parent_formset": parent_formset,
                "enfant_formset": enfant_formset,
            })

        # Détection changements
        def formset_any_change(fs):
            if any(f.has_changed() for f in fs.forms):
                return True
            for f in fs.forms:
                cd = getattr(f, "cleaned_data", {}) or {}
                if cd.get("DELETE"):
                    return True
            initial_count = len(getattr(fs, "initial_forms", []))
            extra_forms = fs.forms[initial_count:]
            if any(f.has_changed() for f in extra_forms):
                return True
            return False

        changed = any([
            famille_form.has_changed(),
            formset_any_change(parent_formset),
            formset_any_change(enfant_formset),
        ])
        if not changed:
            messages.info(request, "Aucun changement détecté.")
            return redirect("famille:manage_account")

        # ---------- Sauvegardes ----------
        if famille_form.has_changed():
            famille_form.save()

        parents_group = _get_group("parents")
        existing_parent_ids = set(self._parents_queryset(famille).values_list("id", flat=True))

        touched_current_user = False

        # Parents
        for form in parent_formset:
            if not form.cleaned_data:
                continue
            del_flag = form.cleaned_data.get("DELETE")
            user_id = form.cleaned_data.get("user_id")
            first = form.cleaned_data.get("first_name")
            last = form.cleaned_data.get("last_name")
            email = form.cleaned_data.get("email")
            new_pwd = form.cleaned_data.get("new_password")

            if user_id:
                user = get_object_or_404(User, pk=user_id)
                if del_flag:
                    if existing_parent_ids - {user.id}:
                        user.delete()
                        existing_parent_ids.discard(user.id)
                    else:
                        messages.error(request, "Impossible de supprimer le dernier parent.")
                        raise transaction.TransactionManagementError("last-parent-guard")
                else:
                    user.first_name = first
                    user.last_name = last
                    user.email = email
                    user.username = email
                    if new_pwd:
                        user.set_password(new_pwd)
                    user.save()
                    if user.pk == request.user.pk:
                        touched_current_user = True
                    user.groups.add(parents_group)
                    UserProfile.objects.get_or_create(user=user, defaults={"famille": famille, "role": "parent"})
            else:
                if del_flag:
                    continue
                password = new_pwd or User.objects.make_random_password()
                new_user = User.objects.create_user(
                    username=email, email=email, password=password,
                    first_name=first, last_name=last
                )
                new_user.groups.add(parents_group)
                UserProfile.objects.create(user=new_user, famille=famille, role="parent")

        # Enfants
        for form in enfant_formset.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                inst = form.instance
                if inst.pk and inst.user:
                    inst.user.delete()
                if inst.pk:
                    inst.delete()
                continue
            inst = form.save(commit=False)
            inst.famille = famille
            inst.save()
            form.save_user(famille)

        logger.warning(f"[ACCOUNT] Before update_session_auth_hash: auth={request.user.is_authenticated} "
                       f"session_key={getattr(request.session, 'session_key', None)} "
                       f"touched_current_user={touched_current_user}")

        if touched_current_user:
            update_session_auth_hash(request, request.user)
            request.user.refresh_from_db()
        
        logger.warning(f"[ACCOUNT] After update_session_auth_hash: auth={request.user.is_authenticated} "
                       f"session_key={getattr(request.session, 'session_key', None)}")

        # Force backend si besoin
        backend = getattr(settings, "AUTHENTICATION_BACKENDS", ["django.contrib.auth.backends.ModelBackend"])[0]
        login(request, request.user, backend=backend)
        request.user.refresh_from_db()

        logger.warning(f"[ACCOUNT][POST] end: auth={request.user.is_authenticated} "
                       f"session_key={getattr(request.session, 'session_key', None)}")

        messages.success(request, "Compte famille mis à jour.")
        return redirect("points:dashboard")

    # ---------- Suppression de MON compte parent ----------
    def _delete_self_parent(self, request, famille):
        me = request.user
        other_parents = self._parents_queryset(famille).exclude(pk=me.pk)
        if not other_parents.exists():
            messages.error(request, "Impossible de supprimer votre compte : vous êtes le dernier parent.")
            return redirect("famille:manage_account")
        me.delete()
        messages.success(request, "Votre compte parent a été supprimé.")
        return redirect("points:dashboard")



family_manage_view = ManageFamilyAccountView.as_view()


# ===================================================================
# ==================   SUPPRESSION TOTALE   =========================
# ===================================================================

class DeleteFamilyView(LoginRequiredMixin, View):
    template_name = "famille/confirm_delete_family.html"

    def _is_parent(self, user):
        try:
            return user.profile.role == "parent"
        except UserProfile.DoesNotExist:
            return False

    def get(self, request):
        if not self._is_parent(request.user):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")
        famille = request.user.profile.famille
        form = FamilyHardDeleteForm()
        return render(request, self.template_name, {"form": form, "famille": famille})

    @transaction.atomic
    def post(self, request):
        if not self._is_parent(request.user):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")

        famille = request.user.profile.famille
        form = FamilyHardDeleteForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "famille": famille})

        # Double confirmation
        if form.cleaned_data["family_name"].strip() != famille.nom.strip():
            form.add_error("family_name", "Le nom ne correspond pas exactement.")
            return render(request, self.template_name, {"form": form, "famille": famille})

        if not request.user.check_password(form.cleaned_data["password"]):
            form.add_error("password", "Mot de passe incorrect.")
            return render(request, self.template_name, {"form": form, "famille": famille})

        # 1) Supprimer tous les utilisateurs (parents/enfants) liés à la famille
        users_qs = User.objects.filter(profile__famille=famille)
        current_user_id = request.user.id
        users_qs.delete()  # CASCADE supprime UserProfile

        # 2) Supprimer la famille (CASCADE supprime Enfant, etc.)
        famille.delete()

        # 3) Déconnexion si user courant supprimé
        if request.user.is_authenticated and request.user.id == current_user_id:
            logout(request)

        messages.success(request, "La famille et tous les comptes associés ont été supprimés définitivement.")
        return redirect("home")  # adapte au nom de ta route d’accueil


family_delete_view = DeleteFamilyView.as_view()
