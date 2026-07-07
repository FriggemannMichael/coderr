import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from offers_app.models import Offer
from profiles_app.models import UserProfile
from reviews_app.models import Review


def create_user(username, profile_type):
    user = get_user_model().objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='StrongPass123!',
    )
    UserProfile.objects.create(user=user, type=profile_type)
    return user


@pytest.mark.django_db
def test_base_info_is_public():
    response = APIClient().get(reverse('base-info'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_base_info_returns_expected_statistics():
    business_one = create_user('business_one', UserProfile.ProfileType.BUSINESS)
    business_two = create_user('business_two', UserProfile.ProfileType.BUSINESS)
    customer = create_user('customer', UserProfile.ProfileType.CUSTOMER)
    Offer.objects.create(user=business_one, title='Logo', description='Package')
    Review.objects.create(
        business_user=business_one,
        reviewer=customer,
        rating=4,
        description='Gut',
    )
    Review.objects.create(
        business_user=business_two,
        reviewer=customer,
        rating=5,
        description='Top',
    )

    response = APIClient().get(reverse('base-info'))

    assert response.status_code == 200
    assert response.data['review_count'] == 2
    assert response.data['average_rating'] == 4.5
    assert response.data['business_profile_count'] == 2
    assert response.data['offer_count'] == 1


@pytest.mark.django_db
def test_base_info_average_rating_is_rounded_to_one_decimal():
    business = create_user('business', UserProfile.ProfileType.BUSINESS)
    c1 = create_user('c1', UserProfile.ProfileType.CUSTOMER)
    c2 = create_user('c2', UserProfile.ProfileType.CUSTOMER)
    c3 = create_user('c3', UserProfile.ProfileType.CUSTOMER)
    Review.objects.create(
        business_user=business, reviewer=c1, rating=5, description='a'
    )
    Review.objects.create(
        business_user=business, reviewer=c2, rating=4, description='b'
    )
    Review.objects.create(
        business_user=business, reviewer=c3, rating=4, description='c'
    )

    response = APIClient().get(reverse('base-info'))

    assert response.status_code == 200
    assert response.data['average_rating'] == 4.3


@pytest.mark.django_db
def test_base_info_empty_returns_stable_values():
    response = APIClient().get(reverse('base-info'))

    assert response.status_code == 200
    assert response.data['review_count'] == 0
    assert response.data['average_rating'] == 0
    assert response.data['business_profile_count'] == 0
    assert response.data['offer_count'] == 0
