import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from catalog.models import Category, Product
from cart.models import Cart

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework.authtoken.models import Token

    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def admin_client(admin_user):
    from rest_framework.test import APIClient

    client = APIClient()
    from rest_framework.authtoken.models import Token

    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Test Category",
        slug="test-category",
        is_active=True,
    )


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="Test Product",
        slug="test-product",
        category=category,
        price=99.99,
        stock=10,
        sku="SKU-001",
        is_active=True,
    )


@pytest.fixture
def cart(db, user):
    return Cart.objects.create(user=user)
