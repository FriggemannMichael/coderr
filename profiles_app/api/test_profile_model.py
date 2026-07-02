import pytest
from django.contrib.auth import get_user_model

from profiles_app.models import UserProfile


@pytest.mark.django_db
def test_user_profile_stores_user_type():
    user = get_user_model().objects.create_user(
        username='business_user',
        email='business@example.com',
        password='StrongPass123!',
    )

    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.BUSINESS,
    )

    assert profile.user == user
    assert profile.type == UserProfile.ProfileType.BUSINESS


@pytest.mark.django_db
def test_user_profile_text_fields_default_to_empty_strings():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )

    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.CUSTOMER,
    )

    assert profile.first_name == ''
    assert profile.last_name == ''
    assert profile.location == ''
    assert profile.tel == ''
    assert profile.description == ''
    assert profile.working_hours == ''


@pytest.mark.django_db
def test_user_profile_file_field_is_optional():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )

    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.CUSTOMER,
    )

    assert not profile.file


@pytest.mark.django_db
def test_user_profile_string_representation_returns_username():
    user = get_user_model().objects.create_user(
        username='customer_user',
        email='customer@example.com',
        password='StrongPass123!',
    )
    profile = UserProfile.objects.create(
        user=user,
        type=UserProfile.ProfileType.CUSTOMER,
    )

    assert str(profile) == user.username
