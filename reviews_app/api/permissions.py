from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUser(BasePermission):
    """Allow access only to authenticated customer users."""

    def has_permission(self, request, view):
        return UserProfile.objects.filter(
            user=request.user,
            type=UserProfile.ProfileType.CUSTOMER,
        ).exists()


class IsReviewOwner(BasePermission):
    """Allow changes only to the reviewer who created the review."""

    def has_object_permission(self, request, view, obj):
        return obj.reviewer == request.user
