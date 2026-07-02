import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase


class TestRegistrationAPI(APITestCase):

    def setUp(self):
        self.url = reverse('registration')

    def test_registration_creates_customer_user_and_returns_token(self):


        payload = {
            'username': 'customer_user',
            'email': 'customer@example.com',
            'password': 'StrongPass123!',
            'repeated_password': 'StrongPass123!',
            'type': 'customer',
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['username'], 'customer_user')
        self.assertEqual(response.data['email'], payload['email'])
        self.assertTrue(response.data['user_id'])
        self.assertTrue(response.data['token'])



    def test_registration_rejects_password_mismatch(self):

        payload = {
            'username': 'customer_user',
            'email': 'customer@example.com',
            'password': 'StrongPass123!',
            'repeated_password': 'DifferentPass123!',
            'type': 'customer',
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username='customer_user').exists())


class TestLoginAPI(APITestCase):

    url = reverse('login')

    def setUp(self):
        self.user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )

    def test_login_returns_token_and_user_data(self):

        payload = {
            'username': 'customer_user',
            'password': 'StrongPass123!',
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertTrue(response.data['token'])


    def test_login_rejects_invalid_password(self):

        payload = {
            'username': 'customer_user',
            'password': 'WrongPass123!',
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, 400)

@pytest.fixture
def client():
    return APIClient()#


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )


@pytest.mark.django_db
def test_registration_creates_customer_user_and_returns_token(client):
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
def test_registration_rejects_password_mismatch(client):

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
def test_login_returns_token_and_user_data(client, user):
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
def test_login_rejects_invalid_password(client, user):
    url = reverse('login')
    payload = {
        'username': 'customer_user',
        'password': 'WrongPass123!',
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 400
