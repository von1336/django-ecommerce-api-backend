import pytest
from django.urls import reverse

from cart.models import Cart, CartItem
from catalog.models import Category, Product
from orders.models import Order, OrderItem


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test", slug="test", is_active=True)


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="Product",
        slug="product",
        category=category,
        price=50.00,
        stock=10,
        sku="SKU-001",
        is_active=True,
    )


@pytest.fixture
def cart_with_item(user, product):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    return cart


@pytest.mark.django_db
class TestOrderCreate:
    def test_create_order_from_cart(self, auth_client, user, cart_with_item, product):
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201
        assert Order.objects.filter(user=user).exists()
        order = Order.objects.get(user=user)
        assert order.total_amount == 100.00
        assert order.items.count() == 1
        product.refresh_from_db()
        assert product.stock == 8

    def test_create_order_empty_cart_fails(self, auth_client, user):
        Cart.objects.create(user=user)
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_create_order_insufficient_stock_fails(self, auth_client, user, product):
        product.stock = 1
        product.save()
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=5)
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestOrderList:
    def test_list_orders(self, auth_client, user, cart_with_item):
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        auth_client.post(url, data, format="json")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestOrderDetail:
    def test_order_detail(self, auth_client, user, cart_with_item):
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        create_resp = auth_client.post(url, data, format="json")
        order_id = create_resp.data["id"]
        detail_url = reverse("orders:detail", kwargs={"order_id": order_id})
        response = auth_client.get(detail_url)
        assert response.status_code == 200
        assert response.data["id"] == order_id
        assert "items" in response.data


@pytest.mark.django_db
class TestOrderCancel:
    def test_cancel_order_restores_stock(self, auth_client, user, cart_with_item, product):
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        create_resp = auth_client.post(url, data, format="json")
        order_id = create_resp.data["id"]
        initial_stock = 10
        product.refresh_from_db()
        assert product.stock == 8
        cancel_url = reverse("orders:cancel", kwargs={"order_id": order_id})
        response = auth_client.put(cancel_url)
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.stock == 10
        order = Order.objects.get(id=order_id)
        assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
class TestOrderStatusUpdate:
    def test_admin_can_update_status(self, auth_client, admin_client, user, cart_with_item):
        url = reverse("orders:list")
        data = {
            "shipping_address": "123 Main St",
            "shipping_city": "Moscow",
            "shipping_postal_code": "123456",
            "phone": "+79991234567",
        }
        create_resp = auth_client.post(url, data, format="json")
        assert create_resp.status_code == 201, create_resp.data
        order_id = create_resp.data["id"]
        status_url = reverse("orders:status", kwargs={"order_id": order_id})
        response = admin_client.put(status_url, {"status": "confirmed"}, format="json")
        assert response.status_code == 200
        order = Order.objects.get(id=order_id)
        assert order.status == Order.Status.CONFIRMED
