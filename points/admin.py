from django.contrib import admin

from .models import PointNegatif, PointPositif, BaremeRecompense, BaremePointPositif, BaremePointNegatif


admin.site.register(PointPositif)
admin.site.register(PointNegatif)
admin.site.register(BaremeRecompense)
admin.site.register(BaremePointPositif)
admin.site.register(BaremePointNegatif)
