from django.urls import reverse
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serialize full offer detail data for writes and detail retrieval."""

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Serialize offer detail references for offer list and detail responses."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'url',
        ]

    def get_url(self, obj):
        return reverse('offerdetail-detail', kwargs={'pk': obj.id})


class UserDetailsSerializer(serializers.Serializer):
    """Serialize compact creator data for offer list responses."""

    first_name = serializers.CharField(source='profile.first_name')
    last_name = serializers.CharField(source='profile.last_name')
    username = serializers.CharField()


class OfferSerializer(serializers.ModelSerializer):
    """Serialize offer writes with nested details and computed summary fields."""

    details = OfferDetailSerializer(many=True, required=False)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'description',
            'image',
            'details',
            'min_price',
            'min_delivery_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'min_price',
            'min_delivery_time',
            'created_at',
            'updated_at',
        ]

    def get_min_price(self, obj):
        prices = [detail.price for detail in obj.details.all()]
        return float(min(prices)) if prices else None

    def get_min_delivery_time(self, obj):
        times = [detail.delivery_time_in_days for detail in obj.details.all()]
        return min(times) if times else None

    def validate(self, attrs):
        if self.instance is None and 'details' not in attrs:
            raise serializers.ValidationError(
                {
                    'details': 'This field is required.',
                }
            )
        return super().validate(attrs)

    def validate_details(self, value):
        if self.instance is not None:
            return self._validate_update_details(value)

        required_types = {'basic', 'standard', 'premium'}
        detail_types = {detail['offer_type'] for detail in value}
        if len(value) != 3 or detail_types != required_types:
            raise serializers.ValidationError(
                'Exactly one basic, standard, and premium detail is required.',
            )
        return value

    def _validate_update_details(self, value):
        for detail in value:
            if 'offer_type' not in detail:
                raise serializers.ValidationError(
                    'Offer type is required to update a detail.',
                )
        return value

    def create(self, validated_data):
        details_data = validated_data.pop('details', None)
        offer = Offer.objects.create(
            user=self.context['request'].user,
            **validated_data,
        )
        self._create_details(offer, details_data)
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', [])
        offer = super().update(instance, validated_data)
        self._update_details(offer, details_data)
        return offer

    def _create_details(self, offer, details_data):
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

    def _update_details(self, offer, details_data):
        for detail_data in details_data:
            offer_type = detail_data.pop('offer_type')
            detail = offer.details.get(offer_type=offer_type)
            for field, value in detail_data.items():
                setattr(detail, field, value)
            detail.save()


class OfferReadSerializer(OfferSerializer):
    """Serialize offers for read endpoints with linked details."""

    details = OfferDetailLinkSerializer(many=True)


class OfferListSerializer(OfferReadSerializer):
    """Serialize paginated offer list entries with compact creator details."""

    user_details = UserDetailsSerializer(source='user')

    class Meta(OfferReadSerializer.Meta):
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details',
        ]
