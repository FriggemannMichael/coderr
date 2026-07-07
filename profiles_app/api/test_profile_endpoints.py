from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from profiles_app.models import UserProfile


@pytest.mark.django_db
def test_authenticated_user_can_get_profile_detail():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.get(url)

    assert response.status_code == 200
    assert set(response.data) == {
        'user',
        'username',
        'first_name',
        'last_name',
        'file',
        'location',
        'tel',
        'description',
        'working_hours',
        'type',
        'email',
        'created_at',
    }
    assert response.data['user'] == user.id
    assert response.data['username'] == user.username
    assert response.data['email'] == user.email
    assert response.data['type'] == UserProfile.ProfileType.BUSINESS
    assert response.data['first_name'] == ''
    assert response.data['last_name'] == ''
    assert response.data['location'] == ''
    assert response.data['tel'] == ''
    assert response.data['description'] == ''
    assert response.data['working_hours'] == ''
    assert response.data['first_name'] is not None
    assert response.data['last_name'] is not None
    assert response.data['location'] is not None
    assert response.data['tel'] is not None
    assert response.data['description'] is not None
    assert response.data['working_hours'] is not None


@pytest.mark.django_db
def test_authenticated_user_can_get_another_users_profile_detail():
    owner = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=owner,
        type=UserProfile.ProfileType.BUSINESS,
    )
    requesting_user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=requesting_user,
        type=UserProfile.ProfileType.CUSTOMER,
    )
    token, _ = Token.objects.get_or_create(user=requesting_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': owner.id})

    response = client.get(url)

    assert response.status_code == 200
    assert response.data['user'] == owner.id
    assert response.data['username'] == owner.username


@pytest.mark.django_db
def test_profile_detail_returns_documented_timestamp_format():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    profile.created_at = datetime(
        2026,
        7,
        7,
        12,
        30,
        45,
        123456,
        tzinfo=timezone.UTC,
    )
    profile.save(update_fields=['created_at'])
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.get(url)

    assert response.status_code == 200
    assert response.data['created_at'] == '2026-07-07T12:30:45Z'


@pytest.mark.django_db
def test_profile_detail_requires_authentication():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    client = APIClient()
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_detail_returns_404_for_missing_profile():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_authenticated_user_can_update_own_profile():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})
    payload = {
        'first_name': 'Max',
        'last_name': 'Mustermann',
        'location': 'Berlin',
        'tel': '987654321',
        'description': 'Updated business description',
        'working_hours': '10-18',
        'email': 'new_email@business.de',
    }

    response = client.patch(url, data=payload, format='json')

    user.refresh_from_db()
    assert response.status_code == 200
    assert set(response.data) == {
        'user',
        'username',
        'first_name',
        'last_name',
        'file',
        'location',
        'tel',
        'description',
        'working_hours',
        'type',
        'email',
        'created_at',
    }
    assert response.data['first_name'] == payload['first_name']
    assert response.data['last_name'] == payload['last_name']
    assert response.data['location'] == payload['location']
    assert response.data['tel'] == payload['tel']
    assert response.data['description'] == payload['description']
    assert response.data['working_hours'] == payload['working_hours']
    assert response.data['email'] == payload['email']
    assert user.email == payload['email']
    assert response.data['type'] == UserProfile.ProfileType.BUSINESS


@pytest.mark.django_db
def test_profile_update_does_not_change_read_only_fields():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.patch(
        url,
        data={
            'user': 999,
            'username': 'changed_user',
            'type': UserProfile.ProfileType.CUSTOMER,
            'first_name': 'Max',
        },
        format='json',
    )

    user.refresh_from_db()
    profile.refresh_from_db()
    assert response.status_code == 200
    assert response.data['user'] == user.id
    assert response.data['username'] == 'business_user'
    assert response.data['type'] == UserProfile.ProfileType.BUSINESS
    assert user.username == 'business_user'
    assert profile.type == UserProfile.ProfileType.BUSINESS
    assert profile.first_name == 'Max'


@pytest.mark.django_db
def test_profile_update_requires_authentication():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = APIClient().patch(url, data={'first_name': 'Max'}, format='json')

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_update_returns_404_for_missing_profile():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.patch(url, data={'first_name': 'Max'}, format='json')

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_cannot_update_another_users_profile():
    owner = get_user_model().objects.create_user(
        username='owner_user',
        email='owner@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=owner,
        type=UserProfile.ProfileType.BUSINESS,
    )
    other_user = get_user_model().objects.create_user(
        username='other_user',
        email='other@example.com',
        password='StrongPass123!',
    )
    token, _ = Token.objects.get_or_create(user=other_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': owner.id})

    response = client.patch(url, data={'first_name': 'Hacked'}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_authenticated_user_can_update_profile_with_form_data():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})

    response = client.patch(
        url,
        data={
            'first_name': 'Max',
            'location': 'Berlin',
        },
        format='multipart',
    )

    assert response.status_code == 200
    assert response.data['first_name'] == 'Max'
    assert response.data['location'] == 'Berlin'


@pytest.mark.django_db
def test_authenticated_user_can_upload_profile_file(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('profile-detail', kwargs={'pk': user.id})
    uploaded_file = SimpleUploadedFile(
        'profile.txt',
        b'profile file content',
        content_type='text/plain',
    )

    response = client.patch(
        url,
        data={
            'file': uploaded_file,
        },
        format='multipart',
    )

    assert response.status_code == 200
    assert response.data['file']


@pytest.mark.django_db
def test_authenticated_user_can_get_business_profile_list():
    business_user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=business_user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    customer_user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=customer_user,
        type=UserProfile.ProfileType.CUSTOMER,
    )
    token, _ = Token.objects.get_or_create(user=business_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('business-profiles')

    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['user'] == business_user.id
    assert response.data[0]['username'] == business_user.username
    assert response.data[0]['type'] == UserProfile.ProfileType.BUSINESS
    assert response.data[0]['first_name'] == ''
    assert response.data[0]['last_name'] == ''
    assert response.data[0]['location'] == ''
    assert response.data[0]['tel'] == ''
    assert response.data[0]['description'] == ''
    assert response.data[0]['working_hours'] == ''


@pytest.mark.django_db
def test_business_profile_list_requires_authentication():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    client = APIClient()
    url = reverse('business-profiles')

    response = client.get(url)

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_get_customer_profile_list():
    business_user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=business_user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    customer_user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=customer_user,
        type=UserProfile.ProfileType.CUSTOMER,
    )
    token, _ = Token.objects.get_or_create(user=customer_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('customer-profiles')

    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert set(response.data[0]) == {
        'user',
        'username',
        'first_name',
        'last_name',
        'file',
        'uploaded_at',
        'type',
    }
    assert response.data[0]['user'] == customer_user.id
    assert response.data[0]['username'] == customer_user.username
    assert response.data[0]['type'] == UserProfile.ProfileType.CUSTOMER
    assert response.data[0]['first_name'] == ''
    assert response.data[0]['last_name'] == ''
    assert response.data[0]['first_name'] is not None
    assert response.data[0]['last_name'] is not None
    assert response.data[0]['uploaded_at']


@pytest.mark.django_db
def test_customer_profile_list_requires_authentication():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.CUSTOMER,
    )
    client = APIClient()
    url = reverse('customer-profiles')

    response = client.get(url)

    assert response.status_code == 401
