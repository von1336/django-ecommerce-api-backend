import pytest
from django.urls import reverse

from catalog.models import Category


@pytest.fixture
def parent_category(db):
    return Category.objects.create(name="Electronics", slug="electronics", is_active=True)


@pytest.fixture
def child_category(db, parent_category):
    return Category.objects.create(
        name="Phones",
        slug="phones",
        parent=parent_category,
        is_active=True,
    )


@pytest.mark.django_db
class TestCategoryList:
    def test_list_categories(self, api_client, parent_category):
        url = reverse("catalog_categories:list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data["results"]) >= 1
        cat = next(c for c in response.data["results"] if c["slug"] == "electronics")
        assert cat["name"] == "Electronics"

    def test_tree_structure(self, api_client, parent_category, child_category):
        url = reverse("catalog_categories:list")
        response = api_client.get(url)
        assert response.status_code == 200
        parent = next(c for c in response.data["results"] if c["slug"] == "electronics")
        assert len(parent["children"]) >= 1
        child = next(c for c in parent["children"] if c["slug"] == "phones")
        assert child["name"] == "Phones"


@pytest.mark.django_db
class TestCategoryDetail:
    def test_category_detail(self, api_client, parent_category):
        url = reverse("catalog_categories:detail", kwargs={"slug": "electronics"})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Electronics"
        assert "products" in response.data

    def test_category_not_found(self, api_client):
        url = reverse("catalog_categories:detail", kwargs={"slug": "nonexistent"})
        response = api_client.get(url)
        assert response.status_code == 404
