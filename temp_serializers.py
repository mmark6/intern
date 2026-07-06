content = """""
User serializers for authentication and data management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, Role
from .validators import (
    validate_username,
    validate_email,
    validate_phone,
    validate_password_strength,
    sanitize_string,
)


class RoleSerializer(serializers.ModelSerializer):
    """"Role serializer.""""
    class Meta:
        model = Role
        fields = ['id', 'name']



class UserSerializer(serializers.ModelSerializer):
    """"User serializer for registration and updates.""""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'role_name', 'is_active', 'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'validators': [validate_username]},
            'email': {'validators': [validate_email]},
        }
    
    def validate_username(self, value):
        value = sanitize_string(value, max_length=30)
        validate_username(value)
        return value
    
    def validate_email(self, value):
        value = sanitize_string(value.lower(), max_length=254)
        validate_email(value)
        return value
    
    def validate_first_name(self, value):
        return sanitize_string(value, max_length=150)
    
    def validate_last_name(self, value):
        return sanitize_string(value, max_length=150)
    
    def validate_phone(self, value):
        if value:
            value = sanitize_string(value, max_length=20)
            validate_phone(value)
        return value
    
    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """"Serializer for user registration with enhanced validation."""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(max_length=30, min_length=3)
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
    
    def validate_username(self, value):
        value = sanitize_string(value, max_length=30)
        validate_username(value)
        return value
    
    def validate_email(self, value):
        value = sanitize_string(value.lower(), max_length=254)
        validate_email(value)
        return value
    
    def validate_password(self, value):
        validate_password_strength(value)
        validate_password(value)
        return value
    
    def validate(self, data):
        if 'password2' in data and data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with user data and input validation."""
    
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {'username': {'required': False}}
    
    def validate_username(self, value):
        return value if value else ""
    
    def validate(self, attrs):
        if 'username' not in attrs or not attrs['username']:
            email = attrs.get('email', '').lower() if attrs.get('email') else ''
            if email:
                try:
                    user = User.objects.get(email__iexact=email)
                    attrs['username'] = user.username
                except User.DoesNotExist:
                    pass
        
        try:
            data = super().validate(attrs)
        except serializers.ValidationError:
            raise serializers.ValidationError({'error': 'Invalid username or password'})
        
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role_name': user.get_role_name(),
        }
        return data
"""
with open('Backend/Uedcl/users/serializers.py', 'w') as f:
    f.write(content)
print('Done')
