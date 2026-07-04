import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail
from profiles_app.models import UserProfile


@pytest.mark.django_db
def test_offer_create_requires_authentication():
    client = APIClient()
    url = reverse('offer-list')

    response = client.post(url, data={}, format='json')

    assert response.status_code == 401


@pytest.mark.django_db
def test_customer_user_cannot_create_offer():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.CUSTOMER,
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-list')

    response = client.post(url, data={}, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_business_user_can_create_offer_with_three_details():
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
    url = reverse('offer-list')
    payload = {
        'title': 'Logo Design',
        'description': 'Professional logo package',
        'details': [
            {
                'title': 'Basic Logo',
                'revisions': 1,
                'delivery_time_in_days': 3,
                'price': '50.00',
                'features': ['one concept'],
                'offer_type': 'basic',
            },
            {
                'title': 'Standard Logo',
                'revisions': 3,
                'delivery_time_in_days': 5,
                'price': '100.00',
                'features': ['two concepts'],
                'offer_type': 'standard',
            },
            {
                'title': 'Premium Logo',
                'revisions': -1,
                'delivery_time_in_days': 7,
                'price': '200.00',
                'features': ['three concepts'],
                'offer_type': 'premium',
            },
        ],
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 201
    assert response.data['title'] == payload['title']
    assert response.data['description'] == payload['description']
    assert response.data['user'] == user.id
    assert len(response.data['details']) == 3


@pytest.mark.django_db
def test_offer_create_requires_exactly_three_details():
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
    url = reverse('offer-list')
    payload = {
        'title': 'Logo Design',
        'description': 'Professional logo package',
        'details': [
            {
                'title': 'Basic Logo',
                'revisions': 1,
                'delivery_time_in_days': 3,
                'price': '50.00',
                'features': ['one concept'],
                'offer_type': 'basic',
            },
        ],
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 400
    assert 'details' in response.data


@pytest.mark.django_db
def test_offer_create_requires_basic_standard_and_premium_details():
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
    url = reverse('offer-list')
    payload = {
        'title': 'Logo Design',
        'description': 'Professional logo package',
        'details': [
            {
                'title': 'Basic Logo',
                'revisions': 1,
                'delivery_time_in_days': 3,
                'price': '50.00',
                'features': ['one concept'],
                'offer_type': 'basic',
            },
            {
                'title': 'Basic Logo 2',
                'revisions': 2,
                'delivery_time_in_days': 4,
                'price': '75.00',
                'features': ['second concept'],
                'offer_type': 'basic',
            },
            {
                'title': 'Premium Logo',
                'revisions': -1,
                'delivery_time_in_days': 7,
                'price': '200.00',
                'features': ['three concepts'],
                'offer_type': 'premium',
            },
        ],
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 400
    assert 'details' in response.data


@pytest.mark.django_db
def test_offer_create_returns_min_price_and_min_delivery_time():
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
    url = reverse('offer-list')
    payload = {
        'title': 'Logo Design',
        'description': 'Professional logo package',
        'details': [
            {
                'title': 'Basic Logo',
                'revisions': 1,
                'delivery_time_in_days': 3,
                'price': '50.00',
                'features': ['one concept'],
                'offer_type': 'basic',
            },
            {
                'title': 'Standard Logo',
                'revisions': 3,
                'delivery_time_in_days': 5,
                'price': '100.00',
                'features': ['two concepts'],
                'offer_type': 'standard',
            },
            {
                'title': 'Premium Logo',
                'revisions': -1,
                'delivery_time_in_days': 7,
                'price': '200.00',
                'features': ['three concepts'],
                'offer_type': 'premium',
            },
        ],
    }

    response = client.post(url, data=payload, format='json')

    assert response.status_code == 201
    assert response.data['min_price'] == '50.00'
    assert response.data['min_delivery_time'] == 3


@pytest.mark.django_db
def test_offer_list_returns_detail_links_only():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=user,
        title='Logo Design',
        description='Professional logo package',
    )
    detail = OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=1,
        delivery_time_in_days=3,
        price='50.00',
        features=['one concept'],
        offer_type='basic',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Standard Logo',
        revisions=3,
        delivery_time_in_days=5,
        price='100.00',
        features=['two concepts'],
        offer_type='standard',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Premium Logo',
        revisions=-1,
        delivery_time_in_days=7,
        price='200.00',
        features=['three concepts'],
        offer_type='premium',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-list')

    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['details'][0] == {
        'id': detail.id,
        'url': f'/api/offerdetails/{detail.id}/',
    }
    assert 'title' not in response.data[0]['details'][0]


@pytest.mark.django_db
def test_authenticated_user_can_get_offer_detail_data():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=user,
        title='Logo Design',
        description='Professional logo package',
    )
    detail = OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=-1,
        delivery_time_in_days=3,
        price='50.00',
        features=['one concept'],
        offer_type='basic',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offerdetail-detail', kwargs={'pk': detail.id})

    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == detail.id
    assert response.data['title'] == detail.title
    assert response.data['revisions'] == -1
    assert response.data['delivery_time_in_days'] == 3
    assert response.data['price'] == '50.00'
    assert response.data['features'] == ['one concept']
    assert response.data['offer_type'] == 'basic'


@pytest.mark.django_db
def test_business_user_cannot_update_another_users_offer():
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
        username='other_business_user',
        email='other@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=other_user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=owner,
        title='Logo Design',
        description='Professional logo package',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=1,
        delivery_time_in_days=3,
        price='50.00',
        features=['one concept'],
        offer_type='basic',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Standard Logo',
        revisions=3,
        delivery_time_in_days=5,
        price='100.00',
        features=['two concepts'],
        offer_type='standard',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Premium Logo',
        revisions=-1,
        delivery_time_in_days=7,
        price='200.00',
        features=['three concepts'],
        offer_type='premium',
    )
    token, _ = Token.objects.get_or_create(user=other_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-detail', kwargs={'pk': offer.id})

    response = client.patch(
        url,
        data={'title': 'Changed Title'},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_business_user_can_update_own_offer():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=user,
        title='Logo Design',
        description='Professional logo package',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=1,
        delivery_time_in_days=3,
        price='50.00',
        features=['one concept'],
        offer_type='basic',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Standard Logo',
        revisions=3,
        delivery_time_in_days=5,
        price='100.00',
        features=['two concepts'],
        offer_type='standard',
    )
    OfferDetail.objects.create(
        offer=offer,
        title='Premium Logo',
        revisions=-1,
        delivery_time_in_days=7,
        price='200.00',
        features=['three concepts'],
        offer_type='premium',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-detail', kwargs={'pk': offer.id})

    response = client.patch(
        url,
        data={'title': 'Updated Logo Design'},
        format='json',
    )

    offer.refresh_from_db()
    assert response.status_code == 200
    assert response.data['title'] == 'Updated Logo Design'
    assert offer.title == 'Updated Logo Design'


@pytest.mark.django_db
def test_business_user_cannot_delete_another_users_offer():
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
        username='other_business_user',
        email='other@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=other_user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=owner,
        title='Logo Design',
        description='Professional logo package',
    )
    token, _ = Token.objects.get_or_create(user=other_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-detail', kwargs={'pk': offer.id})

    response = client.delete(url)

    assert response.status_code == 403
    assert Offer.objects.filter(id=offer.id).exists()


@pytest.mark.django_db
def test_business_user_can_delete_own_offer():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=user,
        title='Logo Design',
        description='Professional logo package',
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse('offer-detail', kwargs={'pk': offer.id})

    response = client.delete(url)

    assert response.status_code == 204
    assert not Offer.objects.filter(id=offer.id).exists()
