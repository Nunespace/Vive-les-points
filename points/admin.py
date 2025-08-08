from django.contrib import admin

from .models import Point_negatif, Point_positif


admin.site.register(Point_positif)
admin.site.register(Point_negatif)


