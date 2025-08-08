# famille/views.py
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


class FamilleEnfantsCreateView(LoginRequiredMixin, CreateView):
    """
    Création de la famille + enfants.
    Empêche de créer une 2e famille si OneToOne déjà présent.
    """
    model = Famille
    form_class = FamilleForm
    template_name = "famille/famille_enfants_form.html"
    success_url = reverse_lazy("famille:detail")  # adapte la route

    def dispatch(self, request, *args, **kwargs):
        if get_user_famille(request.user):
            raise PermissionDenied("Une famille est déjà associée à votre compte.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["enfant_formset"] = EnfantFormSet(self.request.POST or None)
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)  # self.object = Famille
        enfant_formset = EnfantFormSet(self.request.POST, instance=self.object)
        if enfant_formset.is_valid():
            enfant_formset.save()
            return response
        transaction.set_rollback(True)
        return self.form_invalid(form)

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)


famille_enfants_create_view = FamilleEnfantsCreateView.as_view()


class FamilleEnfantsUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edition de la famille du user connecté + ses enfants (pas de pk dans l’URL).
    """
    model = Famille
    form_class = FamilleForm
    template_name = "famille/famille_enfants_form.html"
    success_url = reverse_lazy("famille:detail")

    def get_object(self, queryset=None):
        famille = get_user_famille(self.request.user)
        if not famille and not self.request.user.is_superuser:
            raise PermissionDenied("Aucune famille associée à votre compte.")
        # superuser peut éditer ? À toi de choisir; ici, on lui laisse la main
        return famille or super().get_object(queryset)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["enfant_formset"] = EnfantFormSet(self.request.POST or None, instance=self.object)
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        enfant_formset = EnfantFormSet(self.request.POST, instance=self.object)
        if enfant_formset.is_valid():
            enfant_formset.save()
            return response
        transaction.set_rollback(True)
        return self.form_invalid(form)

    def form_invalid(self, form):
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)


famille_enfants_update_view = FamilleEnfantsUpdateView.as_view()


class EnfantDeleteView(EnfantFamilleMixin, DeleteView):
    model = Enfant
    template_name = "famille/enfant_confirm_delete.html"
    success_url = reverse_lazy("famille:update")  # retour sur formulaire Famille + Enfants


enfant_delete_view = EnfantDeleteView.as_view()
