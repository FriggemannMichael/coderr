from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_user_model().objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password'],
        )
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            data={
                'username': user.username,
                'email': user.email,
                'user_id': user.id,
                'token': token.key,
            },
            status=HTTP_201_CREATED,
        )
