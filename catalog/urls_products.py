from django.urls import path

from . import views

app_name = "catalog_products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    path("featured/", views.ProductFeaturedView.as_view(), name="featured"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    path("<slug:slug>/reviews/", views.ProductReviewCreateView.as_view(), name="reviews"),
]
