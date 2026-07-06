"""
Custom validators for user input sanitization and validation.
"""
import re
import html
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


def validate_username(value):
    """Validate username format and uniqueness."""
    if len(value) < 3:
        raise ValidationError("Username must be at least 3 characters long.")
    if len(value) > 30:
        raise ValidationError("Username cannot be longer than 30 characters.")
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise ValidationError("Username can only contain letters, numbers, periods, hyphens, and underscores.")
    
    User = get_user_model()
    if User.objects.filter(username=value).exists():
        raise ValidationError("Username already exists.")


def validate_email(value):
    """Validate email format and uniqueness."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, value):
        raise ValidationError("Invalid email format.")
    
    User = get_user_model()
    if User.objects.filter(email=value).exists():
        raise ValidationError("Email already exists.")


def validate_phone(value):
    """Validate phone number format."""
    if value:
        phone_regex = r'^[\d\s\-\+\(\)]{7,}$'
        if not re.match(phone_regex, value):
            raise ValidationError("Invalid phone number format.")


def validate_password_strength(password):
    """Validate password meets minimum strength requirements."""
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")

    if len(password) > 128:
        raise ValidationError("Password cannot be longer than 128 characters.")


def sanitize_string(value, max_length=None):
    """Sanitize string input to prevent XSS and injection attacks."""
    if not isinstance(value, str):
        return value
    
    # Remove HTML tags
    value = html.escape(value)
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>\"\'%;)(&+]', '', value)
    
    # Strip whitespace
    value = value.strip()
    
    # Limit length
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_dict(data, max_length=None):
    """Sanitize all string values in a dictionary."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value, max_length)
        else:
            sanitized[key] = value
    return sanitized


def validate_field_length(value, min_length=None, max_length=None):
    """Validate field length constraints."""
    if min_length and len(str(value)) < min_length:
        raise ValidationError(f"Field must be at least {min_length} characters long.")
    
    if max_length and len(str(value)) > max_length:
        raise ValidationError(f"Field cannot be longer than {max_length} characters.")
