from django.urls import reverse
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serialize full offer detail data for writes and detail retrieval."""

    price = serializers.FloatField()

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
    """Serialize offer detail references for offer detail responses."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'url',
        ]

    def get_url(self, obj):
        url = reverse('offerdetail-detail', kwargs={'pk': obj.id})
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class OfferListDetailLinkSerializer(serializers.ModelSerializer):
    """Serialize offer detail references for offer list responses."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'url',
        ]

    def get_url(self, obj):
        return f'/offerdetails/{obj.id}/'


class UserDetailsSerializer(serializers.Serializer):
    """Serialize compact creator data for offer list responses."""

    first_name = serializers.CharField(source='profile.first_name')
    last_name = serializers.CharField(source='profile.last_name')
    username = serializers.CharField()


class OfferSerializer(serializers.ModelSerializer):
    """Serialize offer writes with nested details."""

    details = OfferDetailSerializer(many=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]
        read_only_fields = [
            'id',
        ]

    def validate(self, attrs):
        """Require the full detail set when creating a new offer."""
        if self.instance is None and 'details' not in attrs:
            raise serializers.ValidationError(
                {
                    'details': 'This field is required.',
                }
            )
        return super().validate(attrs)

    def validate_details(self, value):
        """Enforce exactly one basic/standard/premium detail on create."""
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
        """Ensure updated details reference offer types that already exist."""
        existing_types = set(self.instance.details.values_list('offer_type', flat=True))
        for detail in value:
            offer_type = detail.get('offer_type')
            if offer_type is None:
                raise serializers.ValidationError(
                    'Offer type is required to update a detail.',
                )
            if offer_type not in existing_types:
                raise serializers.ValidationError(
                    f'No detail with offer type "{offer_type}" exists for this offer.',
                )
        return value

    def create(self, validated_data):
        """Create the offer for the request user with its nested details."""
        details_data = validated_data.pop('details', None)
        if 'image' in validated_data and validated_data['image'] is None:
            validated_data['image'] = ''
        offer = Offer.objects.create(
            user=self.context['request'].user,
            **validated_data,
        )
        self._create_details(offer, details_data)
        return offer

    def update(self, instance, validated_data):
        """Update the offer and apply changes to its existing details."""
        details_data = validated_data.pop('details', [])
        if 'image' in validated_data and validated_data['image'] is None:
            validated_data['image'] = ''
        offer = super().update(instance, validated_data)
        self._update_details(offer, details_data)
        return offer

    def _create_details(self, offer, details_data):
        """Create the nested detail rows for a newly created offer."""
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

    def _update_details(self, offer, details_data):
        """Apply field updates to each existing detail by offer type."""
        for detail_data in details_data:
            offer_type = detail_data.pop('offer_type')
            detail = offer.details.get(offer_type=offer_type)
            for field, value in detail_data.items():
                setattr(detail, field, value)
            detail.save()


class OfferReadSerializer(OfferSerializer):
    """Serialize offers for read endpoints with linked details."""

    details = OfferDetailLinkSerializer(many=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta(OfferSerializer.Meta):
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
        ]
        read_only_fields = fields

    def get_min_price(self, obj):
        prices = [detail.price for detail in obj.details.all()]
        return float(min(prices)) if prices else None

    def get_min_delivery_time(self, obj):
        times = [detail.delivery_time_in_days for detail in obj.details.all()]
        return min(times) if times else None


class OfferListSerializer(OfferReadSerializer):
    """Serialize paginated offer list entries with compact creator details."""

    details = OfferListDetailLinkSerializer(many=True)
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
