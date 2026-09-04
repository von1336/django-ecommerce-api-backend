from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.CartView.as_view(), name="detail"),
    path("items/", views.CartItemAddView.as_view(), name="add_item"),
    path("items/<int:item_id>/", views.CartItemDetailView.as_view(), name="item_detail"),
    path("clear/", views.CartClearView.as_view(), name="clear"),
]
