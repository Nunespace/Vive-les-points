from django.contrib import admin

from .models import PointNegatif, PointPositif


admin.site.register(PointPositif)
admin.site.register(PointNegatif)
