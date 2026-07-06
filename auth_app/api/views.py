from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(user, status_code):
    """Build the token response returned by registration and login."""
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        data={
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
            'token': token.key,
        },
        status=status_code,
    )


class RegistrationView(APIView):
    """Register a new customer or business user and return an auth token."""

    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return build_auth_response(serializer.save(), HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return an auth token."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return build_auth_response(serializer.validated_data['user'], HTTP_200_OK)
