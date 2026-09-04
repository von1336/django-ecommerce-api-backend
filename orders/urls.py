from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="list"),
    path("<int:order_id>/", views.OrderDetailView.as_view(), name="detail"),
    path("<int:order_id>/cancel/", views.OrderCancelView.as_view(), name="cancel"),
    path("<int:order_id>/status/", views.OrderStatusUpdateView.as_view(), name="status"),
]
