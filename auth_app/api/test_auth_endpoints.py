import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from profiles_app.models import UserProfile


@pytest.mark.django_db
def test_registration_creates_customer_user_and_returns_token():
    client = APIClient()
    url = reverse('registration')
    payload = {
        'username': 'customer_user',
        'email': 'customer@example.com',
        'password': 'StrongPass123!',
        'repeated_password': 'StrongPass123!',
        'type': 'customer',
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 201
    assert response.data['username'] == 'customer_user'
    assert response.data['email'] == payload['email']
    assert response.data['user_id']
    assert response.data['token']
    profile = UserProfile.objects.get(user_id=response.data['user_id'])
    assert profile.type == UserProfile.ProfileType.CUSTOMER


@pytest.mark.django_db
def test_registration_rejects_password_mismatch():
    client = APIClient()
    url = reverse('registration')
    payload = {
        'username': 'customer_user',
        'email': 'customer@example.com',
        'password': 'StrongPass123!',
        'repeated_password': 'DifferentPass123!',
        'type': 'customer',
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 400
    assert not get_user_model().objects.filter(username='customer_user').exists()


@pytest.mark.django_db
def test_login_returns_token_and_user_data():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    client = APIClient()
    url = reverse('login')
    payload = {
        'username': 'customer_user',
        'password': 'StrongPass123!',
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 200
    assert response.data['username'] == user.username
    assert response.data['email'] == user.email
    assert response.data['user_id'] == user.id
    assert response.data['token']


@pytest.mark.django_db
def test_login_rejects_invalid_password():
    get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    client = APIClient()
    url = reverse('login')
    payload = {
        'username': 'customer_user',
        'password': 'WrongPass123!',
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 400
