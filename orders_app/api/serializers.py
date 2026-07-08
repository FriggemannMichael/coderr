from django.shortcuts import get_object_or_404
from rest_framework import serializers

from offers_app.models import OfferDetail
from orders_app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serialize orders and create them from an offer detail."""

    price = serializers.SerializerMethodField()
    offer_detail_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
            'offer_detail_id',
        ]
        read_only_fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'created_at',
            'updated_at',
        ]

    def get_price(self, obj):
        return float(obj.price)

    def validate(self, attrs):
        """Restrict updates to the status field only."""
        if self.instance is not None:
            invalid_fields = set(self.initial_data) - {'status'}
            if invalid_fields:
                raise serializers.ValidationError(
                    {field: 'This field cannot be updated.' for field in invalid_fields}
                )
        return super().validate(attrs)

    def create(self, validated_data):
        """Create an order by copying the referenced offer detail."""
        offer_detail = self._get_offer_detail(validated_data)
        return Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=offer_detail.offer.user,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
        )

    def _get_offer_detail(self, validated_data):
        """Fetch the referenced offer detail or raise a 404."""
        queryset = OfferDetail.objects.select_related('offer', 'offer__user')
        return get_object_or_404(queryset, id=validated_data.pop('offer_detail_id'))
