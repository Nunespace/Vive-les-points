from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("connexion/", views.EmailLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view, name="logout"),
    path("", views.IndexView.as_view(), name="accueil"),
    path("<int:pk>/", views.DetailView.as_view(), name="historique"),
    path("new_points/<int:pk>/", views.new_points_view, name="new_points"),
    path("bareme/", views.bareme, name="bareme"),
]
