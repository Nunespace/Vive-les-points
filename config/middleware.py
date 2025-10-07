# config/middleware.py
from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical_host = getattr(settings, "CANONICAL_HOST", None)
        self.force_https = getattr(settings, "CANONICAL_FORCE_HTTPS", True)

    def __call__(self, request):
        host = request.get_host()
        scheme = "https" if self.force_https else request.scheme

        if self.canonical_host and host != self.canonical_host:
            return HttpResponsePermanentRedirect(f"{scheme}://{self.canonical_host}{request.get_full_path()}")

        if self.force_https and request.scheme != "https":
            return HttpResponsePermanentRedirect(f"https://{host}{request.get_full_path()}")

        return self.get_response(request)
    

from django.shortcuts import render

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "MAINTENANCE_MODE", False):
            return render(request, "maintenance.html", status=503)
        return self.get_response(request)

