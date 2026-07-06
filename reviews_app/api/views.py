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
        return self._filter_by_reviewer(queryset)

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
        business_user_id = self.request.query_params.get('business_user_id')
        if business_user_id:
            return queryset.filter(business_user_id=business_user_id)
        return queryset

    def _filter_by_reviewer(self, queryset):
        reviewer_id = self.request.query_params.get('reviewer_id')
        if reviewer_id:
            return queryset.filter(reviewer_id=reviewer_id)
        return queryset
