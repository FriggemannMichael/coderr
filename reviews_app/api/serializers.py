from rest_framework import serializers

from profiles_app.models import UserProfile
from reviews_app.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serialize review data and validate review creation rules."""

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'reviewer',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        business_user = attrs.get('business_user')
        reviewer = self.context['request'].user
        self._validate_business_user(business_user)
        self._validate_unique_review(business_user, reviewer)
        return super().validate(attrs)

    def create(self, validated_data):
        return Review.objects.create(
            reviewer=self.context['request'].user,
            **validated_data,
        )

    def _validate_business_user(self, business_user):
        is_business_user = UserProfile.objects.filter(
            user=business_user,
            type=UserProfile.ProfileType.BUSINESS,
        ).exists()
        if not is_business_user:
            raise serializers.ValidationError(
                {'business_user': 'Selected user must be a business user.'}
            )

    def _validate_unique_review(self, business_user, reviewer):
        if Review.objects.filter(
            business_user=business_user,
            reviewer=reviewer,
        ).exists():
            raise serializers.ValidationError(
                'You have already reviewed this business user.'
            )


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serialize review updates limited to rating and description."""

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'business_user',
            'reviewer',
            'created_at',
            'updated_at',
        ]
