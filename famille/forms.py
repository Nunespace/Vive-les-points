# famille/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory, BaseFormSet
from django.forms.widgets import HiddenInput
from .models import Famille, Enfant, UserProfile

User = get_user_model()


# ------------------ Auth ------------------ #
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Votre adresse email",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Votre mot de passe",
            }
        ),
    )


# ------------------ Form principal Famille ------------------ #
class FamilleForm(forms.ModelForm):
    class Meta:
        model = Famille
        fields = ["nom"]
        widgets = {"nom": forms.TextInput(attrs={"class": "form-control"})}


# ==============================================================
# ================   INSCRIPTION (création)   ==================
# ==============================================================


class ParentUserForm(forms.Form):
    """
    Formulaires parents pour la page d'inscription.
    On crée des Users (parents) + UserProfile(role=parent).
    """

    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            raise ValidationError("Les mots de passe ne correspondent pas.")
        if (
            data.get("email")
            and User.objects.filter(email__iexact=data["email"]).exists()
        ):
            raise ValidationError("Un compte existe déjà avec cet email.")
        return data


class EnfantSignupForm(forms.Form):
    """
    Formulaires enfants pour la page d'inscription.
    On crée des Enfant (modèle) et, si email saisi, un User enfant lié (OneToOne).
    """

    prenom = forms.CharField(
        label="Prénom",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    
    email = forms.EmailField(
        label="Email (facultatif)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Mot de passe (si email saisi)",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        data = super().clean()
        email, password = data.get("email"), data.get("password")

        if email:
            # 1) Unicité côté User
            try:
                existing_user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                existing_user = None

            # 2) Si un User existe déjà sur cet email, vérifier qu'il n'est pas déjà lié à un Enfant
            if (
                existing_user
                and Enfant.objects.filter(user=existing_user).exists()
            ):
                raise ValidationError(
                    "Cet email est déjà utilisé par un autre enfant."
                )

            # 3) Mot de passe requis si email saisi
            if not password:
                raise ValidationError(
                    "Mot de passe requis si un email enfant est saisi."
                )

        return data


class BaseParentFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            # Compter seulement les formulaires réellement remplis
            if form.has_changed():
                count += 1
        if count == 0:
            raise ValidationError("Ajoutez au moins un parent.")


class BaseEnfantFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if form.has_changed():
                count += 1
        if count == 0:
            raise ValidationError("Ajoutez au moins un enfant.")


# Formsets utilisés sur la page d'inscription
ParentFormSet = formset_factory(
    ParentUserForm, extra=1, can_delete=True, formset=BaseParentFormSet
)
EnfantSignupFormSet = formset_factory(
    EnfantSignupForm, extra=1, can_delete=True, formset=BaseEnfantFormSet
)


# ==============================================================
# ==============   GESTION COMPTE (édition)   ==================
# ==============================================================


class ParentInlineForm(forms.Form):
    """
    Edition des parents (Users existants ou ajout).
    """

    user_id = forms.IntegerField(required=False, widget=HiddenInput)
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    new_password = forms.CharField(
        label="Nouveau mot de passe (optionnel)",
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",  # empêche l'autofill "mot de passe actuel"
                "placeholder": "Laisser vide pour conserver",
            },
        ),
    )
    DELETE = forms.BooleanField(required=False)

    def __init__(self, *args, famille=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.famille = (
            famille  # si tu veux ajouter des validations liées à la famille
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user_id = self.cleaned_data.get("user_id")
        qs = User.objects.filter(email__iexact=email)
        if user_id:
            qs = qs.exclude(pk=user_id)
        if qs.exists():
            raise ValidationError("Un compte existe déjà avec cet email.")
        return email


ParentInlineFormSet = formset_factory(
    ParentInlineForm, extra=0, can_delete=True
)


class EnfantManageForm(forms.ModelForm):
    """
    Edition d'un Enfant (modèle) + gestion du compte User enfant lié (OneToOne).
    """

    # Champs HORS-modèle, pour gérer le compte enfant lié
    email = forms.EmailField(
        label="Email (facultatif)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    new_password = forms.CharField(
        label="Mot de passe (si email saisi)",
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
                "placeholder": "Laisser vide pour conserver",
            },
        ),
    )

    class Meta:
        model = Enfant
        fields = ["prenom", "solde_points"]
        widgets = {
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "solde_points": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir l'email si un User est lié
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["email"].initial = self.instance.user.email

    def clean(self):
        data = super().clean()
        email = data.get("email") or ""
        pwd = data.get("new_password")

        if email:
            # Vérifier l'unicité email côté User (hors l'user déjà lié)
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.user:
                qs = qs.exclude(pk=self.instance.user.pk)
            if qs.exists():
                raise ValidationError(
                    "Un compte utilisateur existe déjà avec cet email."
                )
            # Exiger un mot de passe s'il n'y a pas encore d'user lié
            if not self.instance.user and not pwd:
                raise ValidationError(
                    "Mot de passe requis si un email enfant est saisi."
                )
        return data

    def save_user(self, famille):
        """
        Crée/MAJ/supprime le compte enfant lié selon email/new_password,
        met à jour le Group et le UserProfile.
        """
        email = self.cleaned_data.get("email") or ""
        pwd = self.cleaned_data.get("new_password")

        # Aucun compte voulu → supprimer le lien si existant
        if not email:
            if self.instance.user:
                self.instance.user.delete()
                self.instance.user = None
                self.instance.save(update_fields=["user"])
            return

        # Créer/Màj le User enfant
        if not self.instance.user:
            user = User.objects.create_user(
                username=email, email=email, password=pwd
            )
            self.instance.user = user
            self.instance.save(update_fields=["user"])
        else:
            user = self.instance.user
            user.email = email
            user.username = email
            if pwd:
                user.set_password(pwd)
            user.save()

        # Groupe + profil enfant
        from django.contrib.auth.models import Group

        group_enfant, _ = Group.objects.get_or_create(name="enfant")
        user.groups.add(group_enfant)
        UserProfile.objects.update_or_create(
            user=user, defaults={"famille": famille, "role": "enfant"}
        )


# Inline formset basé sur Enfant (modèle) + notre form personnalisé
EnfantInlineFormSet = inlineformset_factory(
    Famille,
    Enfant,
    form=EnfantManageForm,
    extra=0,
    can_delete=True,
    labels={"DELETE": "Retirer de la famille"},
)


# ------------------ Suppression forte famille ------------------ #
class FamilyHardDeleteForm(forms.Form):
    family_name = forms.CharField(
        label="Tapez le nom de la famille pour confirmer",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nom exact de la famille",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
