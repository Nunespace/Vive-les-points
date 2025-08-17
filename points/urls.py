from django.urls import path

from .views import bareme_view, delete_row, update_cell, DashboardView, historique_editable, new_points_view

app_name = "points"

urlpatterns = [
    path("bareme/", bareme_view, name="bareme"),
    path("cell/<str:model_name>/<int:pk>/<str:field>/", update_cell, name="update_cell"),
    path("delete/<str:model_name>/<int:pk>/", delete_row, name="delete_row"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("<int:pk>/", historique_editable, name="historique"),
    path("new_points/<int:pk>/", new_points_view, name="new_points"),
]
