from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUser(BasePermission):
    """Allow access only to authenticated customer users."""

    def has_permission(self, request, view):
        return UserProfile.objects.filter(
            user=request.user,
            type=UserProfile.ProfileType.CUSTOMER,
        ).exists()


class IsBusinessUser(BasePermission):
    """Allow access only to authenticated business users."""

    def has_permission(self, request, view):
        return UserProfile.objects.filter(
            user=request.user,
            type=UserProfile.ProfileType.BUSINESS,
        ).exists()


class IsOrderBusinessOwner(BasePermission):
    """Allow order changes only for the assigned business user."""

    def has_object_permission(self, request, view, obj):
        return obj.business_user == request.user
