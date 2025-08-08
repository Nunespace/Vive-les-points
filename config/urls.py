# config/urls.py
from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("", include("famille.urls")),
    path("points/", include("points.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
