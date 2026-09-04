from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from catalog.models import Product
from notifications.tasks import send_order_confirmation, send_order_status_update

from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderListSerializer, OrderSerializer, OrderStatusUpdateSerializer


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related("items")
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = list(cart.items.select_related("product"))
        if not items:
            return Response(
                {"error": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        user = request.user

        with transaction.atomic():
            product_ids = [cart_item.product_id for cart_item in items]
            locked_products = {
                p.id: p
                for p in Product.objects.select_for_update().filter(id__in=product_ids)
            }
            for cart_item in items:
                p = locked_products.get(cart_item.product_id)
                if not p or p.stock < cart_item.quantity:
                    return Response(
                        {"error": f"Not enough stock for {cart_item.product.name}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            order = Order.objects.create(
                user=user,
                status=Order.Status.PENDING,
                total_amount=Decimal("0"),
                shipping_address=data["shipping_address"],
                shipping_city=data["shipping_city"],
                shipping_postal_code=data["shipping_postal_code"],
                phone=data["phone"],
                comment=data.get("comment") or "",
            )

            total = Decimal("0")
            for cart_item in items:
                p = locked_products[cart_item.product_id]
                item_total = p.price * cart_item.quantity
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    product_name=p.name,
                    product_price=p.price,
                    quantity=cart_item.quantity,
                    item_total=item_total,
                )
                total += item_total
                p.stock -= cart_item.quantity
                p.save(update_fields=["stock"])

            order.total_amount = total
            order.save(update_fields=["total_amount"])

            cart.items.all().delete()

        try:
            send_order_confirmation.delay(order.id)
        except Exception:
            pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related("items").get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id):
        try:
            order = Order.objects.prefetch_related("items").get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in (Order.Status.PENDING, Order.Status.CONFIRMED):
            return Response(
                {"error": "Only pending or confirmed orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in order.items.all():
                if item.product:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=["stock"])
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status"])

        return Response(OrderSerializer(order).data)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order.status = serializer.validated_data["status"]
        order.save(update_fields=["status"])
        try:
            send_order_status_update.delay(order.id, order.status)
        except Exception:
            pass

        return Response(OrderSerializer(order).data)
