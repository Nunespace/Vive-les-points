from django.contrib import admin

from .models import PointNegatif, PointPositif, BaremeRecompense, BaremePointPositif, BaremePointNegatif


# filtrer par famille
class BaremeRecompenseAdmin(admin.ModelAdmin):
    list_filter = ('famille',)


class BaremePointPositifAdmin(admin.ModelAdmin):
    list_filter = ('famille',)


class BaremePointNegatifAdmin(admin.ModelAdmin):
    list_filter = ('famille',)

# Filtrer par famille dans l'admin


class PointPositifAdmin(admin.ModelAdmin):
    list_filter = ('enfant__famille',)


class PointNegatifAdmin(admin.ModelAdmin):
    list_filter = ('enfant__famille',)


admin.site.register(PointPositif, PointPositifAdmin)
admin.site.register(PointNegatif, PointNegatifAdmin)
admin.site.register(BaremeRecompense, BaremeRecompenseAdmin)
admin.site.register(BaremePointPositif, BaremePointPositifAdmin)
admin.site.register(BaremePointNegatif, BaremePointNegatifAdmin)
