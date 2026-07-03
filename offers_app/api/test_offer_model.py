from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from offers_app.models import Offer, OfferDetail


def create_user(username='business_user', email='business@example.com'):
    return get_user_model().objects.create_user(
        username=username,
        email=email,
        password='StrongPass123!',
    )


def create_offer(user=None):
    return Offer.objects.create(
        user=user or create_user(),
        title='Logo Design',
        description='Professional logo design package',
    )


def create_offer_detail(offer=None, offer_type=OfferDetail.OfferType.BASIC):
    return OfferDetail.objects.create(
        offer=offer or create_offer(),
        title='Basic Logo',
        revisions=2,
        delivery_time_in_days=5,
        price=100,
        features=['Logo design'],
        offer_type=offer_type,
    )


@pytest.mark.django_db
def test_offer_stores_required_fields_and_user_relation():
    user = create_user()

    offer = create_offer(user=user)

    assert offer.user == user
    assert offer.title == 'Logo Design'
    assert offer.description == 'Professional logo design package'


@pytest.mark.django_db
def test_offer_detail_belongs_to_offer_and_stores_required_fields():
    offer = create_offer()

    detail = OfferDetail.objects.create(
        offer=offer,
        title='Basic Logo',
        revisions=2,
        delivery_time_in_days=5,
        price=100,
        features=['One logo concept', 'PNG export'],
        offer_type=OfferDetail.OfferType.BASIC,
    )
    detail.refresh_from_db()

    assert detail.offer == offer
    assert detail.title == 'Basic Logo'
    assert detail.revisions == 2
    assert detail.delivery_time_in_days == 5
    assert detail.price == Decimal('100.00')
    assert detail.features == ['One logo concept', 'PNG export']
    assert detail.offer_type == OfferDetail.OfferType.BASIC


@pytest.mark.django_db
def test_offer_detail_allows_unlimited_revisions_marker():
    detail = OfferDetail(
        offer=create_offer(),
        title='Premium Logo',
        revisions=-1,
        delivery_time_in_days=10,
        price=500,
        features=['Unlimited revisions'],
        offer_type=OfferDetail.OfferType.PREMIUM,
    )

    detail.full_clean()

    assert detail.revisions == -1


@pytest.mark.django_db
def test_offer_detail_rejects_revisions_below_unlimited_marker():
    detail = OfferDetail(
        offer=create_offer(),
        title='Invalid Logo',
        revisions=-2,
        delivery_time_in_days=10,
        price=500,
        features=['Logo design'],
        offer_type=OfferDetail.OfferType.PREMIUM,
    )

    with pytest.raises(ValidationError):
        detail.full_clean()


@pytest.mark.django_db
def test_offer_has_basic_standard_and_premium_details():
    offer = create_offer()

    for offer_type in ['basic', 'standard', 'premium']:
        OfferDetail.objects.create(
            offer=offer,
            title=f'{offer_type.title()} Logo',
            revisions=2,
            delivery_time_in_days=5,
            price=100,
            features=['Logo design'],
            offer_type=offer_type,
        )

    detail_types = set(offer.details.values_list('offer_type', flat=True))

    assert detail_types == {'basic', 'standard', 'premium'}
    assert offer.details.count() == 3


@pytest.mark.django_db
def test_offer_detail_rejects_invalid_offer_type():
    detail = OfferDetail(
        offer=create_offer(),
        title='Invalid Logo',
        revisions=2,
        delivery_time_in_days=5,
        price=100,
        features=['Logo design'],
        offer_type='invalid',
    )

    with pytest.raises(ValidationError):
        detail.full_clean()


@pytest.mark.django_db
def test_offer_cannot_have_duplicate_detail_type():
    offer = create_offer()
    create_offer_detail(offer=offer, offer_type=OfferDetail.OfferType.BASIC)

    with pytest.raises(IntegrityError):
        OfferDetail.objects.create(
            offer=offer,
            title='Second Basic Logo',
            revisions=3,
            delivery_time_in_days=7,
            price=150,
            features=['Second logo design'],
            offer_type=OfferDetail.OfferType.BASIC,
        )


@pytest.mark.django_db
def test_deleting_offer_deletes_offer_details():
    offer = create_offer()
    detail = create_offer_detail(offer=offer)

    offer.delete()

    assert not OfferDetail.objects.filter(id=detail.id).exists()


@pytest.mark.django_db
def test_user_can_access_offers_through_related_name():
    user = create_user()
    offer = create_offer(user=user)

    assert list(user.offers.all()) == [offer]


@pytest.mark.django_db
def test_offer_and_detail_string_representations_are_useful():
    offer = create_offer()
    detail = create_offer_detail(offer=offer)

    assert str(offer) == 'Logo Design'
    assert str(detail) == 'Logo Design - Basic Logo'


def test_offer_models_are_registered_in_admin():
    assert Offer in admin.site._registry
    assert OfferDetail in admin.site._registry
