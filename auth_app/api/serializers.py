from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from profiles_app.models import UserProfile


class RegistrationSerializer(serializers.Serializer):
    """Validate registration input and create a user with a profile."""

    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(
        choices=UserProfile.ProfileType.choices,
        write_only=True,
    )

    def validate_username(self, value):
        """Reject a username that is already taken."""
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with that username already exists.'
            )
        return value

    def validate(self, attrs):
        """Confirm the password and its repetition match."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': ['Passwords do not match.']}
            )
        return attrs

    def create(self, validated_data):
        """Create the user and its matching profile from validated input."""
        validated_data.pop('repeated_password', None)
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        UserProfile.objects.create(
            user=user,
            type=validated_data['type'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Validate credentials and expose the authenticated user."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the credentials and attach the resolved user."""
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if user is None:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})
        attrs['user'] = user
        return attrs
