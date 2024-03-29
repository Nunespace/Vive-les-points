import datetime

from django.db import models
from django.utils import timezone


class Enfant(models.Model):
    prenom = models.CharField(max_length=200)
    solde_points = models.IntegerField(default=0)

    def __str__(self):
        return self.prenom + " " + str(self.solde_points)


class Point_positif(models.Model):
    motif1 = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Motif")
    nb_positif = models.IntegerField(default=0, verbose_name="Nombre")
    date = models.DateField(auto_now=True)
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.enfant} {self.nb_positif} {self.date}'


class Point_negatif(models.Model):
    motif2 = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Motif")
    nb_negatif = models.IntegerField(default=0, verbose_name="Nombre")
    date = models.DateField(auto_now=True)
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.enfant} {self.nb_negatif} {self.date}'


