"""User serializers for authentication and data management."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Role
from .validators import (
    validate_username,
    validate_email,
    validate_phone,
    validate_password_strength,
    sanitize_string,
)


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer."""

    class Meta:
        model = Role
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    """User serializer for registration and updates.

    NOTE: This serializer is also used by admin/API endpoints that create users.
    Therefore it must support setting a password (otherwise created users
    would have unusable/empty passwords and fail login).
    """

    role_name = serializers.CharField(source="role.name", read_only=True)
    role = serializers.CharField(write_only=True, required=False, allow_blank=True)

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=6,
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=6,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "image",
            "role",
            "role_name",
            "is_active",
            "created_at",
            "updated_at",
            "password",
            "password2",
            "email_notifications_enabled",
            "notify_before_days",
        ]

    def validate_username(self, value):
        value = sanitize_string(value, max_length=30)
        # Skip uniqueness check for admin creation
        if not self.context.get('admin_create'):
            validate_username(value)
        return value

    def validate_email(self, value):
        value = sanitize_string(value.lower(), max_length=254)
        # Skip uniqueness check for admin creation
        if not self.context.get('admin_create'):
            validate_email(value)
        return value

    def validate_first_name(self, value):
        return sanitize_string(value, max_length=150)

    def validate_last_name(self, value):
        return sanitize_string(value, max_length=150)

    def validate_phone(self, value):
        if value:
            value = sanitize_string(value, max_length=20)
            # Skip format validation for admin creation
            if not self.context.get('admin_create'):
                validate_phone(value)
        return value

    def validate_password(self, value):
        if value:
            # Validate password strength for admin-created users
            try:
                validate_password_strength(value)
            except ValidationError as e:
                raise e
        return value

    def validate(self, attrs):
        # Only enforce password confirmation when at least one password field is provided.
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password is not None or password2 is not None:
            if not password:
                raise serializers.ValidationError({"password": "Password is required."})
            if password2 and password != password2:
                raise serializers.ValidationError({"password2": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password2", None)

        # Handle role - convert role name to Role object
        role_name = validated_data.pop("role", None)
        if role_name:
            try:
                role = Role.objects.get(name=role_name)
                validated_data["role"] = role
            except Role.DoesNotExist:
                pass  # Role not found, leave as None

        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password2", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={"input_type": "password"},
    )

    password2 = serializers.CharField(
        write_only=True,
        min_length=6,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "phone",
        ]

    def validate_username(self, value):
        value = sanitize_string(value, max_length=30)
        validate_username(value)
        return value

    def validate_email(self, value):
        value = sanitize_string(value.lower(), max_length=254)
        validate_email(value)
        return value

    def validate_first_name(self, value):
        if value:
            return sanitize_string(value, max_length=150)
        return value

    def validate_last_name(self, value):
        if value:
            return sanitize_string(value, max_length=150)
        return value

    def validate_phone(self, value):
        if value:
            value = sanitize_string(value, max_length=20)
            validate_phone(value)
        return value

    def validate_password(self, value):
        validate_password_strength(value)
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")

        import logging
        logger = logging.getLogger(__name__)
        logger.debug('[Register] Creating user: username=%s, email=%s', validated_data.get("username"), validated_data.get("email"))

        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
        )

        user.set_password(validated_data["password"])
        user.save()
        logger.debug('[Register] User created with hashed password')

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    

    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        import logging
        logger = logging.getLogger(__name__)

        # Get username and password from attrs
        login_input = attrs.get("username") or attrs.get("email", "").lower()
        password = attrs.get("password", "")

        if not login_input:
            raise serializers.ValidationError(
                {"error": "Username or email is required"}
            )

        # Try to find user by email first, then by username
        user = None
        if "@" in login_input:
            try:
                user = User.objects.get(email__iexact=login_input.lower())
                logger.debug('[Login] Found user by email: %s', user.username)
            except User.DoesNotExist:
                logger.debug('[Login] No user found with email: %s', login_input)
                pass

        if not user:
            try:
                user = User.objects.get(username__iexact=login_input.lower())
                logger.debug('[Login] Found user by username: %s', user.username)
            except User.DoesNotExist:
                logger.debug('[Login] No user found with username: %s', login_input)
                raise serializers.ValidationError(
                    {"error": "Invalid username/email or password"}
                )

        # Verify the password directly (don't use Django's authenticate)
        if not user.check_password(password):
            logger.debug('[Login] Password verification failed for: %s', user.username)
            raise serializers.ValidationError(
                {"error": "Invalid username/email or password"}
            )

        logger.debug('[Login] Password verified for: %s', user.username)

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"error": "User account is disabled"}
            )

        # Manually generate tokens instead of using super()
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)

        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone or "",
                "image": user.image.url if user.image else None,
                "role_name": user.get_role_name()
                if hasattr(user, "get_role_name")
                else str(user.role),
            },
        }

        return data