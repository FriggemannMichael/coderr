import pytest
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
