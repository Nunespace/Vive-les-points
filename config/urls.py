# config/urls.py
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from famille.views import landing_view, confidentialite_view
from django.shortcuts import render


def maintenance(request):
    return render(request, "famille/maintenance.html", status=503)


urlpatterns = [
    #path("", landing_view, name="landing"),   # Page d'accueil
    path("", maintenance),
    path("confidentialite/", confidentialite_view, name="confidentialite"),
    path("famille/", include("famille.urls")),
    path("points/", include("points.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
