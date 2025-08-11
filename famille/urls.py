# famille/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import email_login_view, register_family_view, family_manage_view, family_delete_view


app_name = "famille"

urlpatterns = [
    path("inscription/", register_family_view, name="famille_register"),
    path("login/", email_login_view, name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("compte/", family_manage_view, name="manage_account"),
    path("supprimer-famille/", DeleteFamilyView.as_view(), name="delete_family"),
    
]
