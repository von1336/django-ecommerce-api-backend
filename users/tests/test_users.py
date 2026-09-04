import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUserRegistration:
    def test_register_success(self, api_client):
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "phone": "+1234567890",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        assert "token" in response.data
        assert response.data["user"]["username"] == "newuser"
        assert response.data["user"]["email"] == "new@example.com"

    def test_register_password_mismatch(self, api_client):
        url = reverse("users:register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "different",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        url = reverse("users:login")
        response = api_client.post(
            url,
            {"username": user.username, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200
        assert "token" in response.data

    def test_login_invalid_credentials(self, api_client, user):
        url = reverse("users:login")
        response = api_client.post(
            url,
            {"username": user.username, "password": "wrongpass"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_success(self, auth_client):
        url = reverse("users:logout")
        response = auth_client.post(url)
        assert response.status_code == 204


@pytest.mark.django_db
class TestProfile:
    def test_get_profile_authenticated(self, auth_client, user):
        url = reverse("users:profile")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["username"] == user.username

    def test_get_profile_unauthenticated(self, api_client):
        url = reverse("users:profile")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_update_profile(self, auth_client, user):
        url = reverse("users:profile")
        data = {"phone": "+9999999999", "city": "Moscow"}
        response = auth_client.put(url, data, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.phone == "+9999999999"
        assert user.city == "Moscow"
