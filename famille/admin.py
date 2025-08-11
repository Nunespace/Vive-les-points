from django.contrib import admin
from .models import Famille, Enfant, UserProfile

# Register your models here.

admin.site.register(Famille)
admin.site.register(UserProfile)
admin.site.register(Enfant)