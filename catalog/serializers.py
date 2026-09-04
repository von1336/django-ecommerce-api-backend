from django.db.models import Avg
from rest_framework import serializers

from .models import Category, Product, ProductImage, Review


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "parent", "is_active", "created_at", "children")

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class CategoryDetailSerializer(CategorySerializer):
    products = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ("products",)

    def get_products(self, obj):
        products = obj.products.filter(is_active=True)[:20]
        return ProductListSerializer(products, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image_url", "alt_text", "is_primary", "position")


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "username", "rating", "text", "created_at")
        read_only_fields = ("user",)

    def validate_rating(self, value):
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "old_price",
            "main_image",
            "avg_rating",
            "review_count",
            "is_in_stock",
        )

    def get_main_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image_url
        first = obj.images.first()
        return first.image_url if first else None

    def get_avg_rating(self, obj):
        result = obj.reviews.aggregate(avg=Avg("rating"))
        return round(result["avg"], 1) if result["avg"] is not None else None

    def get_review_count(self, obj):
        return obj.reviews.count()


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    category = CategoryBriefSerializer(read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    discount_percent = serializers.ReadOnlyField()
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category",
            "price",
            "old_price",
            "stock",
            "sku",
            "is_active",
            "is_featured",
            "created_at",
            "updated_at",
            "images",
            "reviews",
            "is_in_stock",
            "discount_percent",
            "avg_rating",
            "review_count",
        )

    def get_avg_rating(self, obj):
        result = obj.reviews.aggregate(avg=Avg("rating"))
        return round(result["avg"], 1) if result["avg"] is not None else None

    def get_review_count(self, obj):
        return obj.reviews.count()
