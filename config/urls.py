# config/urls.py
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.generic.base import RedirectView


urlpatterns = [
    path("", include("famille.urls")),
    path("points/", include("points.urls")),
    path("admin/", admin.site.urls),
    # Redirection racine vers /login/
    path("", RedirectView.as_view(url="/login/", permanent=True)),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
