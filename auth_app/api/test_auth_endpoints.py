import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient


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
