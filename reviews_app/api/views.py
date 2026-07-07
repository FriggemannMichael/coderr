from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from reviews_app.models import Review

from .permissions import IsCustomerUser, IsReviewOwner
from .serializers import ReviewSerializer, ReviewUpdateSerializer


class ReviewViewSet(ModelViewSet):
    """Provide review list, create, update, and delete endpoints."""

    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.select_related('business_user', 'reviewer')
        queryset = self._filter_by_business_user(queryset)
        queryset = self._filter_by_reviewer(queryset)
        return self._apply_ordering(queryset)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomerUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsReviewOwner()]
        return [IsAuthenticated()]

    def _filter_by_business_user(self, queryset):
        business_user_id = self._get_int_param('business_user_id')
        if business_user_id is not None:
            return queryset.filter(business_user_id=business_user_id)
        return queryset

    def _filter_by_reviewer(self, queryset):
        reviewer_id = self._get_int_param('reviewer_id')
        if reviewer_id is not None:
            return queryset.filter(reviewer_id=reviewer_id)
        return queryset

    def _apply_ordering(self, queryset):
        ordering = self.request.query_params.get('ordering')
        allowed_fields = {
            'updated_at': 'updated_at',
            '-updated_at': '-updated_at',
            'rating': 'rating',
            '-rating': '-rating',
        }
        if ordering in [None, '']:
            return queryset.order_by('-updated_at')
        if ordering not in allowed_fields:
            raise ValidationError({'ordering': 'Unsupported ordering field.'})
        return queryset.order_by(allowed_fields[ordering])

    def _get_int_param(self, name):
        value = self.request.query_params.get(name)
        if value in [None, '']:
            return None
        try:
            return int(value)
        except ValueError as error:
            raise ValidationError({name: 'Must be an integer.'}) from error
