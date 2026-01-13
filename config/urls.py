# config/urls.py
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from famille.views import landing_view, confidentialite_view
from django.shortcuts import render
from django.views.generic import RedirectView


def maintenance(request):
    return render(request, "famille/maintenance.html", status=503)


urlpatterns = [
    path("", landing_view, name="landing"),   # Page d'accueil
    # path("", maintenance),
    path("confidentialite/", confidentialite_view, name="confidentialite"),
    path("famille/", include("famille.urls")),
    path("points/", include("points.urls")),
    path("admin/", admin.site.urls),
    # Redirections pour les anciennes URLs
    path("login/", RedirectView.as_view(url="/famille/login/",permanent=True)),
    path("inscription/", RedirectView.as_view(url="/famille/inscription/",permanent=True),),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
