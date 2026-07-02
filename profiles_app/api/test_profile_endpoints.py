import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
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

    assert response.status_code == 200
    assert response.data['first_name'] == payload['first_name']
    assert response.data['last_name'] == payload['last_name']
    assert response.data['location'] == payload['location']
    assert response.data['tel'] == payload['tel']
    assert response.data['description'] == payload['description']
    assert response.data['working_hours'] == payload['working_hours']
    assert response.data['email'] == payload['email']


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
