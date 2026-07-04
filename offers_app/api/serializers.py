from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
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
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'url',
        ]

    def get_url(self, obj):
        return f'/api/offerdetails/{obj.id}/'


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
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
        return f'{min(detail.price for detail in obj.details.all()):.2f}'

    def get_min_delivery_time(self, obj):
        return min(detail.delivery_time_in_days for detail in obj.details.all())

    def validate_details(self, value):
        required_types = {'basic', 'standard', 'premium'}
        detail_types = {detail['offer_type'] for detail in value}

        if len(value) != 3 or detail_types != required_types:
            raise serializers.ValidationError(
                'Exactly one basic, standard, and premium detail is required.',
            )

        return value

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(
            user=self.context['request'].user,
            **validated_data,
        )
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)

        return offer


class OfferReadSerializer(OfferSerializer):
    details = OfferDetailLinkSerializer(many=True)
