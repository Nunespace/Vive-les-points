import datetime

from django.db import models
from django.utils import timezone
from famille.models import Enfant, Famille


class BaremeRecompense(models.Model):
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE)
    points = models.PositiveIntegerField()
    valeur_euros = models.CharField(max_length=200)
    valeur_temps = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.points} points"


class BaremePointPositif(models.Model):
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE)
    motif = models.CharField(max_length=1000)
    points = models.IntegerField(default=1)  # toujours positif

    def __str__(self):
        return self.motif


class BaremePointNegatif(models.Model):
    famille = models.ForeignKey(Famille, on_delete=models.CASCADE)
    motif = models.CharField(max_length=1000)
    points = models.IntegerField(default=-1)  # toujours négatif

    def __str__(self):
        return self.motif


class PointPositif(models.Model):
    motif1 = models.CharField(
        max_length=1000, null=True, blank=True, verbose_name="Motif"
    )
    nb_positif = models.IntegerField(default=0, verbose_name="Nombre")
    date = models.DateField(default=timezone.now)
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.enfant} {self.nb_positif} {self.date}"


class PointNegatif(models.Model):
    motif2 = models.CharField(
        max_length=1000, null=True, blank=True, verbose_name="Motif"
    )
    nb_negatif = models.IntegerField(default=0, verbose_name="Nombre")
    date = models.DateField(default=timezone.now)
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.enfant} {self.nb_negatif} {self.date}"
