import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail
from profiles_app.models import UserProfile


def create_user(
    username='business_user',
    profile_type=UserProfile.ProfileType.BUSINESS,
    first_name='',
    last_name='',
):
    user = get_user_model().objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(
        user=user,
        type=profile_type,
        first_name=first_name,
        last_name=last_name,
    )
    return user


def authenticated_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


def detail_payload(
    offer_type='basic',
    title='Basic Logo',
    revisions=1,
    delivery_time=3,
    price='50.00',
    features=None,
):
    return {
        'title': title,
        'revisions': revisions,
        'delivery_time_in_days': delivery_time,
        'price': price,
        'features': features or ['one concept'],
        'offer_type': offer_type,
    }


def offer_payload(details=None):
    return {
        'title': 'Logo Design',
        'description': 'Professional logo package',
        'details': details
        or [
            detail_payload(),
            detail_payload(
                offer_type='standard',
                title='Standard Logo',
                revisions=3,
                delivery_time=5,
                price='100.00',
                features=['two concepts'],
            ),
            detail_payload(
                offer_type='premium',
                title='Premium Logo',
                revisions=-1,
                delivery_time=7,
                price='200.00',
                features=['three concepts'],
            ),
        ],
    }


def create_offer_with_details(user, title='Logo Design', price=50, delivery_time=3):
    offer = Offer.objects.create(
        user=user,
        title=title,
        description=f'{title} package',
    )
    for offer_type, detail_price, detail_time in [
        ('basic', price, delivery_time),
        ('standard', price + 50, delivery_time + 2),
        ('premium', price + 100, delivery_time + 4),
    ]:
        OfferDetail.objects.create(
            offer=offer,
            title=f'{title} {offer_type}',
            revisions=1,
            delivery_time_in_days=detail_time,
            price=detail_price,
            features=[offer_type],
            offer_type=offer_type,
        )
    return offer


@pytest.mark.django_db
def test_offer_create_requires_authentication():
    response = APIClient().post(reverse('offer-list'), data={}, format='json')

    assert response.status_code == 401


@pytest.mark.django_db
def test_customer_user_cannot_create_offer():
    user = create_user('customer_user', UserProfile.ProfileType.CUSTOMER)

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data={},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_business_user_can_create_offer_with_three_details():
    user = create_user()
    payload = offer_payload()

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data=payload,
        format='json',
    )

    assert response.status_code == 201
    assert response.data['title'] == payload['title']
    assert response.data['description'] == payload['description']
    assert response.data['user'] == user.id
    assert len(response.data['details']) == 3


@pytest.mark.django_db
def test_offer_create_requires_exactly_three_details():
    user = create_user()
    payload = offer_payload(details=[detail_payload()])

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data=payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'details' in response.data


@pytest.mark.django_db
def test_offer_create_requires_basic_standard_and_premium_details():
    user = create_user()
    payload = offer_payload(
        details=[
            detail_payload(),
            detail_payload(title='Basic Logo 2', revisions=2, price='75.00'),
            detail_payload(
                offer_type='premium',
                title='Premium Logo',
                revisions=-1,
                delivery_time=7,
                price='200.00',
                features=['three concepts'],
            ),
        ],
    )

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data=payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'details' in response.data


@pytest.mark.django_db
def test_offer_create_returns_min_price_and_min_delivery_time():
    user = create_user()

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data=offer_payload(),
        format='json',
    )

    assert response.status_code == 201
    assert response.data['min_price'] == '50.00'
    assert response.data['min_delivery_time'] == 3


@pytest.mark.django_db
def test_offer_list_returns_detail_links_only():
    user = create_user()
    offer = create_offer_with_details(user)
    detail = offer.details.get(offer_type='basic')

    response = authenticated_client(user).get(reverse('offer-list'))

    assert response.status_code == 200
    assert response.data['results'][0]['details'][0] == {
        'id': detail.id,
        'url': f'/api/offerdetails/{detail.id}/',
    }
    assert 'title' not in response.data['results'][0]['details'][0]


@pytest.mark.django_db
def test_authenticated_user_can_get_offer_detail_data():
    user = create_user()
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

    response = authenticated_client(user).get(
        reverse('offerdetail-detail', kwargs={'pk': detail.id}),
    )

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
    owner = create_user('owner_user')
    other_user = create_user('other_business_user')
    offer = create_offer_with_details(owner)

    response = authenticated_client(other_user).patch(
        reverse('offer-detail', kwargs={'pk': offer.id}),
        data={'title': 'Changed Title'},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_business_user_can_update_own_offer():
    user = create_user()
    offer = create_offer_with_details(user)

    response = authenticated_client(user).patch(
        reverse('offer-detail', kwargs={'pk': offer.id}),
        data={'title': 'Updated Logo Design'},
        format='json',
    )

    offer.refresh_from_db()
    assert response.status_code == 200
    assert response.data['title'] == 'Updated Logo Design'
    assert offer.title == 'Updated Logo Design'


@pytest.mark.django_db
def test_business_user_cannot_delete_another_users_offer():
    owner = create_user('owner_user')
    other_user = create_user('other_business_user')
    offer = Offer.objects.create(
        user=owner,
        title='Logo Design',
        description='Professional logo package',
    )

    response = authenticated_client(other_user).delete(
        reverse('offer-detail', kwargs={'pk': offer.id}),
    )

    assert response.status_code == 403
    assert Offer.objects.filter(id=offer.id).exists()


@pytest.mark.django_db
def test_business_user_can_delete_own_offer():
    user = create_user()
    offer = Offer.objects.create(
        user=user,
        title='Logo Design',
        description='Professional logo package',
    )

    response = authenticated_client(user).delete(
        reverse('offer-detail', kwargs={'pk': offer.id}),
    )

    assert response.status_code == 204
    assert not Offer.objects.filter(id=offer.id).exists()


@pytest.mark.django_db
def test_customer_user_can_get_offer_list():
    business_user = create_user('business_user')
    customer_user = create_user('customer_user', UserProfile.ProfileType.CUSTOMER)
    offer = create_offer_with_details(business_user)

    response = authenticated_client(customer_user).get(reverse('offer-list'))

    assert response.status_code == 200
    assert response.data['results'][0]['id'] == offer.id


@pytest.mark.django_db
def test_customer_user_can_get_offer_detail():
    business_user = create_user('business_user')
    customer_user = create_user('customer_user', UserProfile.ProfileType.CUSTOMER)
    offer = create_offer_with_details(business_user)

    response = authenticated_client(customer_user).get(
        reverse('offer-detail', kwargs={'pk': offer.id}),
    )

    assert response.status_code == 200
    assert response.data['id'] == offer.id


@pytest.mark.django_db
def test_offer_detail_collection_endpoint_is_not_available():
    user = create_user()

    response = authenticated_client(user).get('/api/offerdetails/')

    assert response.status_code == 404


@pytest.mark.django_db
def test_authenticated_user_cannot_modify_offer_detail_directly():
    user = create_user()
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
    url = reverse('offerdetail-detail', kwargs={'pk': detail.id})
    client = authenticated_client(user)

    patch_response = client.patch(url, data={'title': 'Changed'}, format='json')
    delete_response = client.delete(url)

    assert patch_response.status_code == 405
    assert delete_response.status_code == 405


@pytest.mark.django_db
def test_business_user_can_update_single_offer_detail_by_type():
    user = create_user()
    offer = create_offer_with_details(user)
    basic_detail = offer.details.get(offer_type='basic')
    payload = {
        'details': [
            {
                'title': 'Basic Logo Updated',
                'revisions': 2,
                'offer_type': 'basic',
            },
        ],
    }

    response = authenticated_client(user).patch(
        reverse('offer-detail', kwargs={'pk': offer.id}),
        data=payload,
        format='json',
    )

    basic_detail.refresh_from_db()
    assert response.status_code == 200
    assert basic_detail.title == 'Basic Logo Updated'
    assert basic_detail.revisions == 2


@pytest.mark.django_db
def test_offer_list_response_is_paginated():
    user = create_user()
    create_offer_with_details(user, 'Logo Design', 50, 3)

    response = APIClient().get(reverse('offer-list'))

    assert response.status_code == 200
    assert set(response.data) == {'count', 'next', 'previous', 'results'}


@pytest.mark.django_db
def test_offer_list_contains_user_details():
    user = create_user('business_user', first_name='Max', last_name='Mustermann')
    create_offer_with_details(user, 'Logo Design', 50, 3)

    response = APIClient().get(reverse('offer-list'))

    assert response.status_code == 200
    assert response.data['results'][0]['user_details'] == {
        'first_name': 'Max',
        'last_name': 'Mustermann',
        'username': 'business_user',
    }


@pytest.mark.django_db
def test_offer_list_filters_by_creator_id():
    first_user = create_user('first_business_user')
    second_user = create_user('second_business_user')
    matching_offer = create_offer_with_details(first_user, 'Logo Design', 50, 3)
    create_offer_with_details(second_user, 'Website Design', 100, 5)
    url = f'{reverse("offer-list")}?creator_id={first_user.id}'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == matching_offer.id


@pytest.mark.django_db
def test_offer_list_filters_by_min_price():
    user = create_user()
    create_offer_with_details(user, 'Cheap Logo', 50, 3)
    matching_offer = create_offer_with_details(user, 'Website Design', 120, 5)
    url = f'{reverse("offer-list")}?min_price=100'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == matching_offer.id


@pytest.mark.django_db
def test_offer_list_filters_by_max_delivery_time():
    user = create_user()
    matching_offer = create_offer_with_details(user, 'Fast Logo', 50, 3)
    create_offer_with_details(user, 'Slow Website', 100, 7)
    url = f'{reverse("offer-list")}?max_delivery_time=5'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == matching_offer.id


@pytest.mark.django_db
def test_offer_list_orders_by_min_price():
    user = create_user()
    expensive_offer = create_offer_with_details(user, 'Website Design', 150, 7)
    cheap_offer = create_offer_with_details(user, 'Logo Design', 50, 3)
    url = f'{reverse("offer-list")}?ordering=min_price'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['results'][0]['id'] == cheap_offer.id
    assert response.data['results'][1]['id'] == expensive_offer.id


@pytest.mark.django_db
def test_offer_list_orders_by_updated_at():
    user = create_user()
    first_offer = create_offer_with_details(user, 'Logo Design', 50, 3)
    second_offer = create_offer_with_details(user, 'Website Design', 150, 7)
    url = f'{reverse("offer-list")}?ordering=updated_at'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['results'][0]['id'] == first_offer.id
    assert response.data['results'][1]['id'] == second_offer.id


@pytest.mark.django_db
def test_offer_list_search_matches_title():
    user = create_user()
    matching_offer = create_offer_with_details(user, 'Logo Design', 50, 3)
    create_offer_with_details(user, 'Website Build', 150, 7)
    url = f'{reverse("offer-list")}?search=logo'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == matching_offer.id


@pytest.mark.django_db
def test_offer_list_search_matches_description():
    user = create_user()
    matching_offer = create_offer_with_details(user, 'Logo Design', 50, 3)
    matching_offer.description = 'Custom brand identity package'
    matching_offer.save(update_fields=['description'])
    create_offer_with_details(user, 'Website Build', 150, 7)
    url = f'{reverse("offer-list")}?search=identity'

    response = APIClient().get(url)

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == matching_offer.id


@pytest.mark.django_db
def test_offer_list_invalid_creator_id_returns_400():
    url = f'{reverse("offer-list")}?creator_id=abc'

    response = APIClient().get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_offer_list_invalid_min_price_returns_400():
    url = f'{reverse("offer-list")}?min_price=abc'

    response = APIClient().get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_offer_list_invalid_max_delivery_time_returns_400():
    url = f'{reverse("offer-list")}?max_delivery_time=abc'

    response = APIClient().get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_business_user_cannot_create_offer_without_details():
    user = create_user()
    payload = {
        'title': 'Logo Design',
        'description': 'Professional logo package',
    }

    response = authenticated_client(user).post(
        reverse('offer-list'),
        data=payload,
        format='json',
    )

    assert response.status_code == 400
    assert 'details' in response.data
