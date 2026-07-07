import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail
from orders_app.models import Order
from profiles_app.models import UserProfile


def create_user(username='user', profile_type=UserProfile.ProfileType.CUSTOMER):
    user = get_user_model().objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def authenticated_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


def create_offer_detail():
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    offer = Offer.objects.create(
        user=business_user,
        title='Logo Design',
        description='Professional logo package',
    )
    return OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=3,
        delivery_time_in_days=5,
        price='150.00',
        features=['Logo Design', 'Visitenkarten'],
        offer_type='basic',
    )


def create_order(customer_user, business_user, status=Order.Status.IN_PROGRESS):
    return Order.objects.create(
        customer_user=customer_user,
        business_user=business_user,
        title='Logo Design',
        revisions=3,
        delivery_time_in_days=5,
        price='150.00',
        features=['Logo Design'],
        offer_type='basic',
        status=status,
    )


def create_staff_user(username='staff_user'):
    return get_user_model().objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='StrongPass123!',
        is_staff=True,
    )


@pytest.mark.django_db
def test_customer_user_can_create_order_from_offer_detail():
    customer_user = create_user()
    offer_detail = create_offer_detail()

    response = authenticated_client(customer_user).post(
        reverse('order-list'),
        data={'offer_detail_id': offer_detail.id},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['customer_user'] == customer_user.id
    assert response.data['business_user'] == offer_detail.offer.user.id
    assert response.data['title'] == offer_detail.title
    assert response.data['revisions'] == offer_detail.revisions
    assert response.data['delivery_time_in_days'] == offer_detail.delivery_time_in_days
    assert response.data['price'] == 150.0
    assert response.data['features'] == offer_detail.features
    assert response.data['offer_type'] == offer_detail.offer_type
    assert response.data['status'] == 'in_progress'


@pytest.mark.django_db
def test_business_user_cannot_create_order():
    business_user = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    offer_detail = create_offer_detail()

    response = authenticated_client(business_user).post(
        reverse('order-list'),
        data={'offer_detail_id': offer_detail.id},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_order_create_requires_authentication():
    offer_detail = create_offer_detail()

    response = APIClient().post(
        reverse('order-list'),
        data={'offer_detail_id': offer_detail.id},
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_order_create_requires_offer_detail_id():
    customer_user = create_user()

    response = authenticated_client(customer_user).post(
        reverse('order-list'),
        data={},
        format='json',
    )

    assert response.status_code == 400
    assert 'offer_detail_id' in response.data


@pytest.mark.django_db
def test_order_create_unknown_offer_detail_returns_404():
    customer_user = create_user()

    response = authenticated_client(customer_user).post(
        reverse('order-list'),
        data={'offer_detail_id': 999999},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_user_can_list_only_own_orders():
    customer_user = create_user('customer_user')
    other_customer = create_user('other_customer')
    offer_detail = create_offer_detail()
    own_order = Order.objects.create(
        customer_user=customer_user,
        business_user=offer_detail.offer.user,
        title=offer_detail.title,
        revisions=offer_detail.revisions,
        delivery_time_in_days=offer_detail.delivery_time_in_days,
        price=offer_detail.price,
        features=offer_detail.features,
        offer_type=offer_detail.offer_type,
    )
    Order.objects.create(
        customer_user=other_customer,
        business_user=offer_detail.offer.user,
        title='Other Order',
        revisions=1,
        delivery_time_in_days=3,
        price='50.00',
        features=['other'],
        offer_type='basic',
    )

    response = authenticated_client(customer_user).get(reverse('order-list'))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == own_order.id


@pytest.mark.django_db
def test_order_list_requires_authentication():
    response = APIClient().get(reverse('order-list'))

    assert response.status_code == 401


@pytest.mark.django_db
def test_business_user_can_list_only_own_orders():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    other_business_user = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    own_order = create_order(customer_user, business_user)
    create_order(customer_user, other_business_user)

    response = authenticated_client(business_user).get(reverse('order-list'))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == own_order.id


@pytest.mark.django_db
def test_business_user_can_update_order_status():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = authenticated_client(business_user).patch(
        reverse('order-detail', kwargs={'pk': order.id}),
        data={'status': 'completed'},
        format='json',
    )

    order.refresh_from_db()
    assert response.status_code == 200
    assert response.data['status'] == 'completed'
    assert order.status == 'completed'


@pytest.mark.django_db
def test_customer_user_cannot_update_order_status():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = authenticated_client(customer_user).patch(
        reverse('order-detail', kwargs={'pk': order.id}),
        data={'status': 'completed'},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_order_status_update_requires_authentication():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = APIClient().patch(
        reverse('order-detail', kwargs={'pk': order.id}),
        data={'status': 'completed'},
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_order_status_update_rejects_invalid_status():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = authenticated_client(business_user).patch(
        reverse('order-detail', kwargs={'pk': order.id}),
        data={'status': 'not_a_real_status'},
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_order_status_update_unknown_returns_404():
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)

    response = authenticated_client(business_user).patch(
        reverse('order-detail', kwargs={'pk': 999999}),
        data={'status': 'completed'},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_user_can_delete_order():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)
    staff_user = create_staff_user()

    response = authenticated_client(staff_user).delete(
        reverse('order-detail', kwargs={'pk': order.id}),
    )

    assert response.status_code == 204
    assert not Order.objects.filter(id=order.id).exists()


@pytest.mark.django_db
def test_non_staff_user_cannot_delete_order():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = authenticated_client(business_user).delete(
        reverse('order-detail', kwargs={'pk': order.id}),
    )

    assert response.status_code == 403
    assert Order.objects.filter(id=order.id).exists()


@pytest.mark.django_db
def test_order_delete_requires_authentication():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    order = create_order(customer_user, business_user)

    response = APIClient().delete(
        reverse('order-detail', kwargs={'pk': order.id}),
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_order_delete_unknown_returns_404():
    staff_user = create_staff_user()

    response = authenticated_client(staff_user).delete(
        reverse('order-detail', kwargs={'pk': 999999}),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_order_count_returns_in_progress_count():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    create_order(customer_user, business_user, status=Order.Status.IN_PROGRESS)
    create_order(customer_user, business_user, status=Order.Status.IN_PROGRESS)
    create_order(customer_user, business_user, status=Order.Status.COMPLETED)

    response = authenticated_client(customer_user).get(
        reverse('order-count', kwargs={'business_user_id': business_user.id}),
    )

    assert response.status_code == 200
    assert response.data == {'order_count': 2}


@pytest.mark.django_db
def test_order_count_requires_authentication():
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)

    response = APIClient().get(
        reverse('order-count', kwargs={'business_user_id': business_user.id}),
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_order_count_unknown_business_user_returns_404():
    customer_user = create_user('customer_user')

    response = authenticated_client(customer_user).get(
        reverse('order-count', kwargs={'business_user_id': 999999}),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_order_count_for_non_business_user_returns_404():
    customer_user = create_user('customer_user')

    response = authenticated_client(customer_user).get(
        reverse('order-count', kwargs={'business_user_id': customer_user.id}),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_completed_order_count_returns_completed_count():
    customer_user = create_user('customer_user')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    create_order(customer_user, business_user, status=Order.Status.COMPLETED)
    create_order(customer_user, business_user, status=Order.Status.IN_PROGRESS)

    response = authenticated_client(customer_user).get(
        reverse(
            'completed-order-count',
            kwargs={'business_user_id': business_user.id},
        ),
    )

    assert response.status_code == 200
    assert response.data == {'completed_order_count': 1}


@pytest.mark.django_db
def test_completed_order_count_requires_authentication():
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)

    response = APIClient().get(
        reverse(
            'completed-order-count',
            kwargs={'business_user_id': business_user.id},
        ),
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_completed_order_count_unknown_business_user_returns_404():
    customer_user = create_user('customer_user')

    response = authenticated_client(customer_user).get(
        reverse('completed-order-count', kwargs={'business_user_id': 999999}),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_business_user_cannot_update_another_users_order():
    customer_user = create_user('customer_user')
    owner = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    other_business = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    order = create_order(customer_user, owner)

    response = authenticated_client(other_business).patch(
        reverse('order-detail', kwargs={'pk': order.id}),
        data={'status': 'completed'},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_order_list_does_not_crash_for_user_without_profile():
    user = get_user_model().objects.create_user(
        username='no_profile_user',
        email='no_profile@example.com',
        password='StrongPass123!',
    )

    response = authenticated_client(user).get(reverse('order-list'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_order_create_forbidden_for_user_without_profile():
    user = get_user_model().objects.create_user(
        username='no_profile_user',
        email='no_profile@example.com',
        password='StrongPass123!',
    )
    offer_detail = create_offer_detail()

    response = authenticated_client(user).post(
        reverse('order-list'),
        data={'offer_detail_id': offer_detail.id},
        format='json',
    )

    assert response.status_code == 403
