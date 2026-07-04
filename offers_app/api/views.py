from decimal import Decimal, InvalidOperation

from django.db.models import Min, Q
from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from offers_app.models import Offer, OfferDetail

from .permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferReadSerializer,
    OfferSerializer,
)


class OfferPagination(PageNumberPagination):
    """Paginate offer lists with frontend-controlled page size."""

    page_size = 6
    page_size_query_param = 'page_size'


class OfferViewSet(ModelViewSet):
    """Provide documented offer list, detail, create, update, and delete APIs."""

    pagination_class = OfferPagination

    def get_queryset(self):
        queryset = self._base_queryset()
        queryset = self._apply_filters(queryset)
        return self._apply_ordering(queryset)

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated(), IsBusinessUser()]
        if self.action in ['partial_update', 'update', 'destroy']:
            return [IsAuthenticated(), IsOfferOwnerOrReadOnly()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return OfferListSerializer
        if self.action == 'retrieve':
            return OfferReadSerializer

        return OfferSerializer

    def _base_queryset(self):
        return (
            Offer.objects.select_related('user', 'user__profile')
            .prefetch_related(
                'details',
            )
            .annotate(
                min_price_value=Min('details__price'),
                min_delivery_time_value=Min('details__delivery_time_in_days'),
            )
        )

    def _apply_filters(self, queryset):
        queryset = self._filter_creator(queryset)
        queryset = self._filter_price(queryset)
        queryset = self._filter_delivery_time(queryset)
        return self._filter_search(queryset)

    def _filter_creator(self, queryset):
        creator_id = self._get_int_param('creator_id')
        return queryset.filter(user_id=creator_id) if creator_id else queryset

    def _filter_price(self, queryset):
        min_price = self._get_decimal_param('min_price')
        if min_price is None:
            return queryset
        return queryset.filter(min_price_value__gte=min_price)

    def _filter_delivery_time(self, queryset):
        max_time = self._get_int_param('max_delivery_time')
        if max_time is None:
            return queryset
        return queryset.filter(min_delivery_time_value__lte=max_time)

    def _filter_search(self, queryset):
        search = self.request.query_params.get('search')
        if not search:
            return queryset
        return queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search),
        )

    def _apply_ordering(self, queryset):
        ordering = self.request.query_params.get('ordering')
        allowed_fields = {
            'updated_at': 'updated_at',
            '-updated_at': '-updated_at',
            'min_price': 'min_price_value',
            '-min_price': '-min_price_value',
        }
        return queryset.order_by(allowed_fields.get(ordering, '-updated_at'))

    def _get_int_param(self, name):
        value = self.request.query_params.get(name)
        if value in [None, '']:
            return None
        try:
            return int(value)
        except ValueError as error:
            raise ValidationError({name: 'Must be an integer.'}) from error

    def _get_decimal_param(self, name):
        value = self.request.query_params.get(name)
        if value in [None, '']:
            return None
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise ValidationError({name: 'Must be a decimal number.'}) from error


class OfferDetailViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    """Expose only the documented offer detail retrieve endpoint."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
