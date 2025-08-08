# famille/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import email_login_view, famille_enfants_create_view, famille_enfants_update_view, enfant_delete_view


app_name = "famille"

urlpatterns = [
    path("login/", email_login_view, name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("creer/", famille_enfants_create_view, name="create"),
    path("modifier/", famille_enfants_update_view, name="update"),  # pas de pk
    path("famille/", famille_enfants_update_view, name="detail"),           # alias pratique
    path("enfant/<int:pk>/supprimer/", enfant_delete_view, name="enfant_delete"),
]
