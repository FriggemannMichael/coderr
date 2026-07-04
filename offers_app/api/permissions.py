from rest_framework.permissions import SAFE_METHODS, BasePermission

from profiles_app.models import UserProfile


class IsBusinessUser(BasePermission):
    def has_permission(self, request, view):
        return UserProfile.objects.filter(
            user=request.user,
            type=UserProfile.ProfileType.BUSINESS,
        ).exists()


class IsOfferOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user
