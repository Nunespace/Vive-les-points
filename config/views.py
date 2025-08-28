from django.shortcuts import render
# from sentry_sdk import capture_message

from django.http import HttpResponse


def en_construction(request):
    return HttpResponse("<h1>🚧 Site en construction 🚧</h1><p>Contact : nunespace@gmail.com</p>")



def handler404(request, exception):
    "Renvoie une page personnalisée 404 en cas d'erreur de page non trouvée"
    # capture_message("This page was not found.", level="error")
    #capture_message(f"404 Error: Page non trouvée - {request.path}", level="error")  # Ajout de l'URL
    return render(request, '404.html', status=404)


def handler403(request, exception):
    "Renvoie une page personnalisée 403 en cas d'erreur d'interdiction d'accès"
    #capture_message("Vous n'avez pas les droits pour accéder à cette page.", level="error")
    return render(request, '403.html', status=403)


def handler500(request):
    "Renvoie une page personnalisée 500 en cas d'erreur de serveur interne"
    #capture_message("Page not found : erreur serveur!", level="error")
    return render(request, '500.html', status=500)