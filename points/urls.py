from django.urls import path

from . import views

app_name = "points"

urlpatterns = [
    path("bareme/", views.bareme_view, name="bareme"),
    path("bareme/<str:model_name>/<int:pk>/<str:field>/", views.update_cell, name="update_cell"),
    path("", views.IndexView.as_view(), name="dashboard"),
    path("<int:pk>/", views.historique_editable, name="historique"),
    path("new_points/<int:pk>/", views.new_points_view, name="new_points"),
    
]
