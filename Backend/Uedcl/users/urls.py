"""
URL configuration for the User app.

Note: `me/` and `register/`, `login/`, `logout/`, `roles/` must precede the
generic `<int:pk>/` pattern so they don't get swallowed by the integer matcher.
"""
from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, MeView,
    UserListCreateView, UserDetailView,
    RoleListCreateView, UserImageView,
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='users-register'),
    path('login/', LoginView.as_view(), name='users-login'),
    path('logout/', LogoutView.as_view(), name='users-logout'),
    path('me/', MeView.as_view(), name='users-me'),
    path('me/image/', UserImageView.as_view(), name='users-me-image'),


    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),


    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
