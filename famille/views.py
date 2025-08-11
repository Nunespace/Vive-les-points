# famille/views.py
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import render, redirect
from django.views import View

from .forms import FamilleForm, ParentFormSet, EnfantFormSet
from .models import Famille, Enfant, UserProfile
from django.contrib.auth import get_user_model
from django.utils.html import format_html, format_html_join


from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import Famille, Enfant
from .forms import EmailAuthenticationForm, FamilleForm, EnfantFormSet
from .mixins import get_user_famille, EnfantFamilleMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db import transaction
from django.conf import settings

from .models import Famille, Enfant, UserProfile
from .forms import FamilleForm, ParentInlineFormSet, EnfantFormSet, FamilyHardDeleteForm
User = get_user_model()


class EmailLoginView(LoginView):
    template_name = "famille/login.html"
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        messages.success(self.request, "Connexion réussie. Bienvenue !")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Identifiants invalides.")
        return super().form_invalid(form)


email_login_view = EmailLoginView.as_view()


def _get_group(name):
    # S'assure que les groupes existent (parents, enfant)
    group, _ = Group.objects.get_or_create(name=name)
    return group

class RegisterFamilyView(View):
    template_name = "famille/register.html"

    def get(self, request):
        ctx = {
            "famille_form": FamilleForm(),
            "parent_formset": ParentFormSet(prefix="parents"),
            "enfant_formset": EnfantFormSet(prefix="enfants"),
        }
        return render(request, self.template_name, ctx)

    from django.utils.html import format_html

    @transaction.atomic
    def post(self, request):
        famille_form = FamilleForm(request.POST)
        parent_formset = ParentFormSet(request.POST, prefix="parents")
        enfant_formset = EnfantFormSet(request.POST, prefix="enfants")

        if not (famille_form.is_valid() and parent_formset.is_valid() and enfant_formset.is_valid()):
            error_messages = []

            for field, errors in famille_form.errors.items():
                for err in errors:
                    error_messages.append(f"Famille - {field}: {err}")

            for i, form in enumerate(parent_formset.forms, start=1):
                for field, errors in form.errors.items():
                    for err in errors:
                        error_messages.append(f"Parent {i} - {field}: {err}")

            for i, form in enumerate(enfant_formset.forms, start=1):
                for field, errors in form.errors.items():
                    for err in errors:
                        error_messages.append(f"Enfant {i} - {field}: {err}")

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


        # 1) Créer la famille
        famille = famille_form.save()

        # 2) Créer les parents (Users + UserProfile + groupe)
        parents_group = _get_group("parents")
        enfants_group = _get_group("enfant")

        created_parent_user = None
        for form in parent_formset:
            if form.cleaned_data.get("DELETE"):
                continue
            cd = form.cleaned_data
            user = User.objects.create_user(
                username=cd["email"],  # si vous utilisez email comme identifiant
                email=cd["email"],
                password=cd["password1"],
                first_name=cd["first_name"],
                last_name=cd["last_name"],
            )
            user.groups.add(parents_group)
            UserProfile.objects.create(user=user, famille=famille, role="parent")
            if created_parent_user is None:
                created_parent_user = user  # on connecte le 1er parent

        # 3) Créer les enfants (Enfant + optionnellement User + UserProfile)
        for form in enfant_formset:
            if form.cleaned_data.get("DELETE"):
                continue
            cd = form.cleaned_data
            enfant_obj = Enfant.objects.create(
                prenom=cd["prenom"],
                solde_points=cd["solde_points"] or 0,
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
                # (optionnel) relier Enfant<->UserProfile si vous ajoutez un FK plus tard

        messages.success(request, "Famille et utilisateurs créés avec succès.")
        # 4) Connecter le 1er parent créé
        if created_parent_user:
            login(request, created_parent_user, backend="unique_user_email.backend.EmailBackend")

        return redirect("points:dashboard")


register_family_view = RegisterFamilyView.as_view()


class ManageFamilyAccountView(LoginRequiredMixin, View):
    template_name = "famille/account_manage.html"

    def _require_parent(self, request):
        try:
            return request.user.profile  # OneToOne
        except UserProfile.DoesNotExist:
            return None

    def _ensure_parent_access(self, request):
        profile = self._require_parent(request)
        return profile and profile.role == "parent"

    def _parents_queryset(self, famille):
        return User.objects.filter(profile__famille=famille, profile__role="parent").order_by("id")

    def get(self, request):
        if not self._ensure_parent_access(request):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")

        famille = request.user.profile.famille

        # Famille form
        famille_form = FamilleForm(instance=famille)

        # Parents -> initial pour FormSet
        parents = self._parents_queryset(famille)
        parent_initial = [{
            "user_id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "DELETE": False,
        } for u in parents]
        parent_formset = ParentInlineFormSet(initial=parent_initial, prefix="parents")

        # Enfants formset
        enfant_formset = EnfantFormSet(instance=famille, prefix="enfants")

        return render(request, self.template_name, {
            "famille_form": famille_form,
            "parent_formset": parent_formset,
            "enfant_formset": enfant_formset,
        })

    @transaction.atomic
    def post(self, request):
        if not self._ensure_parent_access(request):
            messages.error(request, "Accès réservé aux parents.")
            return redirect("points:dashboard")

        famille = request.user.profile.famille

        # Gestion suppression de "mon compte" parent
        if "delete_self" in request.POST:
            return self._delete_self_parent(request, famille)

        famille_form = FamilleForm(request.POST, instance=famille)
        parent_formset = ParentInlineFormSet(request.POST, prefix="parents")
        enfant_formset = EnfantFormSet(request.POST, instance=famille, prefix="enfants")

        # injecter contexte famille pour validations email (ParentInlineForm.clean_email)
        for form in parent_formset:
            form.famille = famille

        is_valid = famille_form.is_valid() and parent_formset.is_valid() and enfant_formset.is_valid()
        if not is_valid:
            messages.error(request, "Merci de corriger les erreurs dans le formulaire.")
            return render(request, self.template_name, {
                "famille_form": famille_form,
                "parent_formset": parent_formset,
                "enfant_formset": enfant_formset,
            })

        # 1) Famille
        famille_form.save()

        # 2) Parents (update / delete / add)
        parents_group = _get_group("parents")
        existing_parent_ids = set(self._parents_queryset(famille).values_list("id", flat=True))
        to_keep_ids = set()

        for form in parent_formset:
            if not form.cleaned_data:  # forms supprimés par management_form
                continue

            del_flag = form.cleaned_data.get("DELETE")
            user_id = form.cleaned_data.get("user_id")
            first_name = form.cleaned_data.get("first_name")
            last_name  = form.cleaned_data.get("last_name")
            email      = form.cleaned_data.get("email")
            new_pwd    = form.cleaned_data.get("new_password")

            if user_id:  # édition / suppression d'un parent existant
                user = get_object_or_404(User, pk=user_id)
                if del_flag:
                    # garde-fou: empêcher de supprimer le dernier parent
                    if existing_parent_ids - {user.id}:
                        # OK il reste d'autres parents
                        user.delete()  # cascade supprime UserProfile grâce au OneToOne
                        existing_parent_ids.discard(user.id)
                    else:
                        messages.error(request, "Impossible de supprimer le dernier parent. Ajoutez d'abord un autre parent.")
                        raise transaction.TransactionManagementError("last-parent-guard")
                else:
                    # update
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.username = email  # si email = identifiant
                    if new_pwd:
                        user.set_password(new_pwd)
                    user.save()
                    # s’assurer du group + profil
                    user.groups.add(parents_group)
                    UserProfile.objects.get_or_create(user=user, defaults={"famille": famille, "role": "parent"})
                    to_keep_ids.add(user.id)
            else:
                if del_flag:
                    continue  # ligne vide marquée delete : ignorer
                # ajout d'un nouveau parent
                password = new_pwd or User.objects.make_random_password()
                new_user = User.objects.create_user(
                    username=email, email=email, password=password,
                    first_name=first_name, last_name=last_name
                )
                new_user.groups.add(parents_group)
                UserProfile.objects.create(user=new_user, famille=famille, role="parent")
                to_keep_ids.add(new_user.id)
                existing_parent_ids.add(new_user.id)

        # 3) Enfants
        enfant_formset.save()

        messages.success(request, "Compte famille mis à jour.")
        return redirect("famille:manage_account")

    def _delete_self_parent(self, request, famille):
        """Supprime le compte du parent connecté (mais pas la famille).
           Empêche de supprimer si c’est le dernier parent restant.
        """
        me = request.user
        other_parents_qs = self._parents_queryset(famille).exclude(pk=me.pk)

        if not other_parents_qs.exists():
            messages.error(request, "Impossible de supprimer votre compte : vous êtes le dernier parent de la famille.")
            return redirect("famille:manage_account")

        # OK, on supprime le compte du parent courant
        me.delete()  # cascade supprime UserProfile
        messages.success(request, "Votre compte parent a été supprimé.")
        return redirect("points:dashboard")


family_manage_view = ManageFamilyAccountView.as_view()


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

        # OK — suppression totale
        # 1) Supprimer tous les utilisateurs liés à la famille (parents + enfants ayant un compte)
        users_qs = User.objects.filter(profile__famille=famille)
        # On garde l'id du user courant pour vérifier l’état de session après suppression
        current_user_id = request.user.id
        users_qs.delete()  # CASCADE supprime UserProfile

        # 2) Supprimer la famille (CASCADE supprimera Enfant, Point, etc. liés à Famille)
        famille.delete()

        # 3) Déconnecter proprement si l’utilisateur courant vient d’être supprimé
        # (users_qs.delete() a supprimé le user, la session n’est plus valide)
        if request.user.is_authenticated and request.user.id == current_user_id:
            logout(request)

        messages.success(request, "La famille et tous les comptes associés ont été supprimés définitivement.")
        return redirect("home")  # ⬅️ adapte ce nom de route (page d’accueil)

family_delete_view = DeleteFamilyView.as_view()