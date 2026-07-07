import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from profiles_app.models import UserProfile
from reviews_app.models import Review


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


def create_review(reviewer, business_user, rating=4, description='Alles war toll!'):
    return Review.objects.create(
        business_user=business_user,
        reviewer=reviewer,
        rating=rating,
        description=description,
    )


@pytest.mark.django_db
def test_customer_user_can_create_review_for_business_user():
    customer_user = create_user()
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )

    response = authenticated_client(customer_user).post(
        reverse('review-list'),
        data={
            'business_user': business_user.id,
            'rating': 4,
            'description': 'Alles war toll!',
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['business_user'] == business_user.id
    assert response.data['reviewer'] == customer_user.id
    assert response.data['rating'] == 4
    assert response.data['description'] == 'Alles war toll!'


@pytest.mark.django_db
def test_business_user_cannot_create_review():
    reviewer = create_user(
        'bussiness_reviewer',
        UserProfile.ProfileType.BUSINESS,
    )
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )

    response = authenticated_client(reviewer).post(
        reverse('review-list'),
        data={
            'business_user': business_user.id,
            'rating': 4,
            'description': 'Alles war toll!',
        },
        format='json',
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_without_profile_cannot_create_review():
    user_without_profile = get_user_model().objects.create_user(
        username='no_profile',
        email='no_profile@example.com',
        password='StrongPass123!',
    )
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)

    response = authenticated_client(user_without_profile).post(
        reverse('review-list'),
        data={
            'business_user': business_user.id,
            'rating': 4,
            'description': 'Alles war toll!',
        },
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_review_create_requires_authentication():
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )

    response = APIClient().post(
        reverse('review-list'),
        data={
            'business_user': business_user.id,
            'rating': 4,
            'description': 'Alles war toll!',
        },
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_customer_user_cannot_review_same_bussines_user_twice():
    customer_user = create_user()
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    Review.objects.create(
        business_user=business_user,
        reviewer=customer_user,
        rating=5,
        description='Schon bewertet.',
    )

    response = authenticated_client(customer_user).post(
        reverse('review-list'),
        data={
            'business_user': business_user.id,
            'rating': 4,
            'description': 'Nochmal  bewertet.',
        },
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_review_create_rejects_non_business_user():
    customer_user = create_user()
    non_business_user = create_user('other_customer')

    response = authenticated_client(customer_user).post(
        reverse('review-list'),
        data={
            'business_user': non_business_user.id,
            'rating': 4,
            'description': 'Alles war toll!',
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'business_user' in response.data


@pytest.mark.django_db
def test_review_list_requires_authentication():
    response = APIClient().get(reverse('review-list'))

    assert response.status_code == 401


@pytest.mark.django_db
def test_authenticated_user_can_list_reviews():
    reviewer = create_user('reviewer')
    business_user = create_user(
        'business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    review = create_review(reviewer, business_user)

    response = authenticated_client(reviewer).get(reverse('review-list'))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == review.id
    assert response.data[0]['business_user'] == business_user.id
    assert response.data[0]['reviewer'] == reviewer.id
    assert response.data[0]['rating'] == 4
    assert response.data[0]['description'] == 'Alles war toll!'
    assert 'created_at' in response.data[0]
    assert 'updated_at' in response.data[0]


@pytest.mark.django_db
def test_review_list_filters_by_business_user_id():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    other_business_user = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    matching_review = create_review(reviewer, business_user)
    create_review(reviewer, other_business_user)

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?business_user_id={business_user.id}',
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == matching_review.id


@pytest.mark.django_db
def test_review_list_filters_by_reviewer_id():
    reviewer = create_user('reviewer')
    other_reviewer = create_user('other_reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    other_business_user = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    matching_review = create_review(reviewer, business_user)
    create_review(other_reviewer, other_business_user)

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?reviewer_id={reviewer.id}',
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == matching_review.id


@pytest.mark.django_db
def test_review_list_orders_by_rating():
    reviewer = create_user('reviewer')
    first_business_user = create_user(
        'first_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    second_business_user = create_user(
        'second_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    low_rating_review = create_review(reviewer, first_business_user, rating=2)
    high_rating_review = create_review(reviewer, second_business_user, rating=5)

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?ordering=rating',
    )

    assert response.status_code == 200
    assert response.data[0]['id'] == low_rating_review.id
    assert response.data[1]['id'] == high_rating_review.id


@pytest.mark.django_db
def test_review_list_orders_by_updated_at():
    reviewer = create_user('reviewer')
    first_business_user = create_user(
        'first_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    second_business_user = create_user(
        'second_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    first_review = create_review(reviewer, first_business_user)
    second_review = create_review(reviewer, second_business_user)

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?ordering=updated_at',
    )

    assert response.status_code == 200
    assert response.data[0]['id'] == first_review.id
    assert response.data[1]['id'] == second_review.id


@pytest.mark.django_db
def test_review_list_invalid_business_user_id_returns_400():
    reviewer = create_user('reviewer')

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?business_user_id=abc',
    )

    assert response.status_code == 400
    assert 'business_user_id' in response.data


@pytest.mark.django_db
def test_review_list_invalid_reviewer_id_returns_400():
    reviewer = create_user('reviewer')

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?reviewer_id=abc',
    )

    assert response.status_code == 400
    assert 'reviewer_id' in response.data


@pytest.mark.django_db
def test_review_list_invalid_ordering_returns_400():
    reviewer = create_user('reviewer')

    response = authenticated_client(reviewer).get(
        f'{reverse("review-list")}?ordering=description',
    )

    assert response.status_code == 400
    assert 'ordering' in response.data


@pytest.mark.django_db
def test_review_owner_can_update_rating_and_description():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = authenticated_client(reviewer).patch(
        reverse('review-detail', kwargs={'pk': review.id}),
        data={'rating': 5, 'description': 'Noch besser als erwartet!'},
        format='json',
    )

    review.refresh_from_db()
    assert response.status_code == 200
    assert response.data['rating'] == 5
    assert review.rating == 5
    assert review.description == 'Noch besser als erwartet!'


@pytest.mark.django_db
def test_non_owner_cannot_update_review():
    reviewer = create_user('reviewer')
    other_customer = create_user('other_customer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = authenticated_client(other_customer).patch(
        reverse('review-detail', kwargs={'pk': review.id}),
        data={'rating': 1},
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_review_update_requires_authentication():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = APIClient().patch(
        reverse('review-detail', kwargs={'pk': review.id}),
        data={'rating': 5},
        format='json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_review_update_rejects_invalid_rating():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = authenticated_client(reviewer).patch(
        reverse('review-detail', kwargs={'pk': review.id}),
        data={'rating': 7},
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_review_update_unknown_returns_404():
    reviewer = create_user('reviewer')

    response = authenticated_client(reviewer).patch(
        reverse('review-detail', kwargs={'pk': 999999}),
        data={'rating': 5},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_review_update_cannot_change_business_user():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    other_business_user = create_user(
        'other_business_user',
        UserProfile.ProfileType.BUSINESS,
    )
    review = create_review(reviewer, business_user)

    response = authenticated_client(reviewer).patch(
        reverse('review-detail', kwargs={'pk': review.id}),
        data={'business_user': other_business_user.id, 'rating': 3},
        format='json',
    )

    review.refresh_from_db()
    assert response.status_code == 200
    assert review.business_user_id == business_user.id


@pytest.mark.django_db
def test_review_owner_can_delete_own_review():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = authenticated_client(reviewer).delete(
        reverse('review-detail', kwargs={'pk': review.id}),
    )

    assert response.status_code == 204
    assert not Review.objects.filter(id=review.id).exists()


@pytest.mark.django_db
def test_non_owner_cannot_delete_review():
    reviewer = create_user('reviewer')
    other_customer = create_user('other_customer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = authenticated_client(other_customer).delete(
        reverse('review-detail', kwargs={'pk': review.id}),
    )

    assert response.status_code == 403
    assert Review.objects.filter(id=review.id).exists()


@pytest.mark.django_db
def test_review_delete_requires_authentication():
    reviewer = create_user('reviewer')
    business_user = create_user('business_user', UserProfile.ProfileType.BUSINESS)
    review = create_review(reviewer, business_user)

    response = APIClient().delete(
        reverse('review-detail', kwargs={'pk': review.id}),
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_review_delete_unknown_returns_404():
    reviewer = create_user('reviewer')

    response = authenticated_client(reviewer).delete(
        reverse('review-detail', kwargs={'pk': 999999}),
    )

    assert response.status_code == 404
