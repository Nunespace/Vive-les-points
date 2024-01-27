from django.contrib import admin

from .models import Enfant, Point_negatif, Point_positif

admin.site.register(Enfant)
admin.site.register(Point_positif)
admin.site.register(Point_negatif)


