from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles_app.models import UserProfile

from .serializers import UserProfileSerializer


class ProfileDetailView(APIView):
    """Retrieve or update a single user profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user_id=pk)
        serializer = self.serializer_class(profile)
        return Response(serializer.data)

    def patch(self, request, pk):
        profile = get_object_or_404(UserProfile, user_id=pk)
        if profile.user_id != request.user.id:
            raise PermissionDenied()

        serializer = self.serializer_class(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BusinessProfileListView(APIView):
    """List all business user profiles."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        profiles = UserProfile.objects.filter(
            type=UserProfile.ProfileType.BUSINESS,
        )
        serializer = self.serializer_class(profiles, many=True)
        return Response(serializer.data)


class CustomerProfileListView(APIView):
    """List all customer user profiles."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        profiles = UserProfile.objects.filter(
            type=UserProfile.ProfileType.CUSTOMER,
        )
        serializer = self.serializer_class(profiles, many=True)
        return Response(serializer.data)
