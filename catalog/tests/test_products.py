import pytest
from django.urls import reverse

from catalog.models import Category, Product, ProductImage, Review
from users.models import User


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category", slug="test-category", is_active=True)


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
        is_featured=False,
    )


@pytest.fixture
def featured_product(db, category):
    return Product.objects.create(
        name="Featured Product",
        slug="featured-product",
        category=category,
        price=199.99,
        stock=5,
        sku="SKU-002",
        is_active=True,
        is_featured=True,
    )


@pytest.mark.django_db
class TestProductList:
    def test_list_products(self, api_client, product):
        url = reverse("catalog_products:list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_filter_by_category(self, api_client, product, category):
        url = reverse("catalog_products:list")
        response = api_client.get(url, {"category": category.id})
        assert response.status_code == 200
        assert all(p["slug"] for p in response.data["results"])

    def test_filter_by_price_range(self, api_client, product):
        url = reverse("catalog_products:list")
        response = api_client.get(url, {"min_price": 50, "max_price": 150})
        assert response.status_code == 200

    def test_search(self, api_client, product):
        url = reverse("catalog_products:list")
        response = api_client.get(url, {"search": "Test"})
        assert response.status_code == 200

    def test_ordering(self, api_client, product):
        url = reverse("catalog_products:list")
        response = api_client.get(url, {"ordering": "price"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestProductDetail:
    def test_product_detail(self, api_client, product):
        url = reverse("catalog_products:detail", kwargs={"slug": "test-product"})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Test Product"
        assert response.data["price"] == "99.99"
        assert "images" in response.data
        assert "reviews" in response.data

    def test_product_not_found(self, api_client):
        url = reverse("catalog_products:detail", kwargs={"slug": "nonexistent"})
        response = api_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestProductReviews:
    def test_add_review(self, auth_client, product, user):
        url = reverse("catalog_products:reviews", kwargs={"slug": "test-product"})
        response = auth_client.post(url, {"rating": 5, "text": "Great product!"}, format="json")
        assert response.status_code == 201
        assert response.data["rating"] == 5
        assert Review.objects.filter(product=product, user=user).exists()

    def test_add_review_duplicate_fails(self, auth_client, product, user):
        Review.objects.create(product=product, user=user, rating=4, text="First")
        url = reverse("catalog_products:reviews", kwargs={"slug": "test-product"})
        response = auth_client.post(url, {"rating": 5, "text": "Second"}, format="json")
        assert response.status_code == 400

    def test_add_review_requires_auth(self, api_client, product):
        url = reverse("catalog_products:reviews", kwargs={"slug": "test-product"})
        response = api_client.post(url, {"rating": 5, "text": "Great!"}, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestFeaturedProducts:
    def test_featured_list(self, api_client, featured_product):
        url = reverse("catalog_products:featured")
        response = api_client.get(url)
        assert response.status_code == 200
        slugs = [p["slug"] for p in response.data["results"]]
        assert "featured-product" in slugs
