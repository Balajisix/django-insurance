from django.urls import path

from .views import (
    CustomerDetailView,
    CustomerListCreateView,
)

app_name = "customers"

urlpatterns = [
    path("", CustomerListCreateView.as_view(), name="customer-list-create",),
    path("<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
]