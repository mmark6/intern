from django.urls import path
from .views import (
    LoginView, RegisterView, logout_view, me_view, TokenRefreshCookieView,
    password_reset_request_view, password_reset_verify_view, password_reset_confirm_view
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='login-register'),
    path('login/', LoginView.as_view(), name='login-login'),
    path('logout/', logout_view, name='login-logout'),
    path('me/', me_view, name='login-me'),
    path('refresh/', TokenRefreshCookieView.as_view(), name='login-refresh'),
    path('password-reset-request/', password_reset_request_view, name='password-reset-request'),
    path('password-reset-verify/', password_reset_verify_view, name='password-reset-verify'),
    path('password-reset-confirm/', password_reset_confirm_view, name='password-reset-confirm'),
]

