from django.db import models
from django.conf import settings  # système de configuration global de Django


class Famille(models.Model):
    """
    Modèle représentant une famille.
    """
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la famille")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_famille",
    )
    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Famille"
        verbose_name_plural = "Familles"
        ordering = ['nom']


class Enfant(models.Model):
    prenom = models.CharField(max_length=200)
    solde_points = models.IntegerField(default=0)
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE)

    def __str__(self):
        return self.prenom + " " + str(self.solde_points)