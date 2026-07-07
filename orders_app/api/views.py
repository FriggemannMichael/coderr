from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from orders_app.models import Order
from profiles_app.models import UserProfile

from .permissions import IsBusinessUser, IsCustomerUser, IsOrderBusinessOwner
from .serializers import OrderSerializer


class OrderViewSet(ModelViewSet):
    """Provide list, create, status update, and delete for orders."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related('customer_user', 'business_user')
        user = self.request.user
        if self.action in ['update', 'partial_update', 'destroy'] or user.is_staff:
            return queryset
        if self._is_customer(user):
            return queryset.filter(customer_user=user)
        return queryset.filter(business_user=user)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomerUser()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsBusinessUser(), IsOrderBusinessOwner()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def _is_customer(self, user):
        return UserProfile.objects.filter(
            user=user,
            type=UserProfile.ProfileType.CUSTOMER,
        ).exists()


class BaseOrderCountView(APIView):
    """Return an order count for a business user filtered by status."""

    permission_classes = [IsAuthenticated]
    order_status = None
    response_key = None

    def get(self, request, business_user_id):
        get_object_or_404(
            UserProfile,
            user_id=business_user_id,
            type=UserProfile.ProfileType.BUSINESS,
        )
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status=self.order_status,
        ).count()
        return Response({self.response_key: count})


class OrderCountView(BaseOrderCountView):
    """Return the number of in-progress orders for a business user."""

    order_status = Order.Status.IN_PROGRESS
    response_key = 'order_count'


class CompletedOrderCountView(BaseOrderCountView):
    """Return the number of completed orders for a business user."""

    order_status = Order.Status.COMPLETED
    response_key = 'completed_order_count'
