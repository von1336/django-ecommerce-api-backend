from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ProductFilter
from .models import Category, Product, Review
from .serializers import CategoryDetailSerializer, CategorySerializer, ProductDetailSerializer, ProductListSerializer, ReviewSerializer


class CategoryListView(ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True, is_active=True)
    serializer_class = CategorySerializer


class CategoryDetailView(RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategoryDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"


class ProductListView(ListAPIView):
    queryset = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images", "reviews")
    serializer_class = ProductListSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "avg_rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        from django.db.models import Avg

        qs = super().get_queryset()
        ordering = self.request.query_params.get("ordering")
        if ordering in ("rating", "avg_rating", "-rating", "-avg_rating"):
            qs = qs.annotate(avg_rating=Avg("reviews__rating"))
            if ordering in ("-rating", "-avg_rating"):
                qs = qs.order_by("-avg_rating")
            else:
                qs = qs.order_by("avg_rating")
        return qs


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images", "reviews")
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"


class ProductFeaturedView(ListAPIView):
    queryset = Product.objects.filter(is_active=True, is_featured=True).select_related("category").prefetch_related("images", "reviews")
    serializer_class = ProductListSerializer


class ProductReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewSerializer(data=request.data, context={"request": request, "product": product})
        if serializer.is_valid():
            if Review.objects.filter(product=product, user=request.user).exists():
                return Response(
                    {"error": "You have already reviewed this product."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
