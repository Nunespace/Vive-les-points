from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="accueil"),
    path("<int:pk>/", views.DetailView.as_view(), name="historique"),
    path("new_points/<int:pk>/", views.new_points_view, name="new_points"),
    path("bareme/", views.bareme, name="bareme"),
]
