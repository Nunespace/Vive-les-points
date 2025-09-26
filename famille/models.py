from django.db import models
from django.conf import settings  # système de configuration global de Django
from django.contrib.auth.models import User


class Famille(models.Model):
    nom = models.CharField(max_length=150)

    def __str__(self):
        return self.nom


class UserProfile(models.Model):
    ROLE_CHOICES = (("parent", "Parent"), ("enfant", "Enfant"))
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    famille = models.ForeignKey(
        Famille, on_delete=models.CASCADE, related_name="membres"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role}) - {self.famille}"


class Enfant(models.Model):
    prenom = models.CharField(max_length=200)
    solde_points = models.IntegerField(default=0)
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE, related_name="enfants")
    user = models.OneToOneField(  # <-- NOUVEAU
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profil_enfant",
    )

    def __str__(self):
        return f"{self.prenom} {self.solde_points}"
