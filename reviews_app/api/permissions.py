from rest_framework.permissions import BasePermission

from profiles_app.models import UserProfile


class IsCustomerUser(BasePermission):
    """Allow access only to authenticated customer users."""

    def has_permission(self, request, view):
        return request.user.profile.type == UserProfile.ProfileType.CUSTOMER


class IsReviewOwner(BasePermission):
    """Allow changes only to the reviewer who created the review."""

    def has_object_permission(self, request, view, obj):
        return obj.reviewer == request.user
