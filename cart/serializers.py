from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductListSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    item_total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "item_total", "added_at")


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Product not found.")
        return value

    def validate(self, attrs):
        product = Product.objects.get(id=attrs["product_id"])
        if product.stock < attrs["quantity"]:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} items available in stock."}
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ("id", "items", "total_price", "total_items", "created_at", "updated_at")
