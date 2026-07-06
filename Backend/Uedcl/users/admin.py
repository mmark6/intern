from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Role


class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(required=True)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data.get('role')
        if commit:
            user.save()
            # Automatically create outstanding JWT refresh token on user creation
            RefreshToken.for_user(user)
        return user


class CustomUserChangeForm(UserChangeForm):
    
    email = forms.EmailField(required=True)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'is_active', 'is_staff')


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
   
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    actions = ['generate_tokens']
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2', 'is_active', 'is_staff')
        }),
    )

    def generate_tokens(self, request, queryset):
        """Generate outstanding JWT refresh tokens for selected users."""
        for user in queryset:
            RefreshToken.for_user(user)
        self.message_user(request, 'Outstanding JWT refresh tokens generated for selected users.', level=messages.SUCCESS)
    generate_tokens.short_description = 'Generate outstanding JWT refresh tokens'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin configuration for role selection."""
    list_display = ('name',)
    search_fields = ('name',)
