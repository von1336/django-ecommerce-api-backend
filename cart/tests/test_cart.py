import pytest
from django.urls import reverse

from cart.models import Cart, CartItem
from catalog.models import Category, Product


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


@pytest.mark.django_db
class TestCartGet:
    def test_get_cart_creates_if_not_exists(self, auth_client, user):
        url = reverse("cart:detail")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert "items" in response.data
        assert Cart.objects.filter(user=user).exists()

    def test_get_cart_returns_items(self, auth_client, user, product):
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        url = reverse("cart:detail")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["quantity"] == 2


@pytest.mark.django_db
class TestCartAddItem:
    def test_add_item(self, auth_client, user, product):
        Cart.objects.create(user=user)
        url = reverse("cart:add_item")
        response = auth_client.post(url, {"product_id": product.id, "quantity": 2}, format="json")
        assert response.status_code == 201
        assert CartItem.objects.filter(cart__user=user, product=product).exists()
        item = CartItem.objects.get(cart__user=user, product=product)
        assert item.quantity == 2

    def test_add_item_stock_check(self, auth_client, user, product):
        product.stock = 2
        product.save()
        Cart.objects.create(user=user)
        url = reverse("cart:add_item")
        response = auth_client.post(url, {"product_id": product.id, "quantity": 5}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestCartUpdateItem:
    def test_update_quantity(self, auth_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=product, quantity=2)
        url = reverse("cart:item_detail", kwargs={"item_id": item.id})
        response = auth_client.put(url, {"quantity": 5}, format="json")
        assert response.status_code == 200
        item.refresh_from_db()
        assert item.quantity == 5

    def test_update_exceeds_stock(self, auth_client, user, product):
        product.stock = 3
        product.save()
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        url = reverse("cart:item_detail", kwargs={"item_id": item.id})
        response = auth_client.put(url, {"quantity": 10}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestCartRemoveItem:
    def test_remove_item(self, auth_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        url = reverse("cart:item_detail", kwargs={"item_id": item.id})
        response = auth_client.delete(url)
        assert response.status_code == 204
        assert not CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
class TestCartClear:
    def test_clear_cart(self, auth_client, user, product):
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        url = reverse("cart:clear")
        response = auth_client.delete(url)
        assert response.status_code == 204
        assert cart.items.count() == 0
