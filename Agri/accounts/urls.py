# urls.py - UPDATED
from django.urls import path
from .views import login_view, signup_view, logout_view, otp_verify_view, resend_otp

urlpatterns = [
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),
    path("otp/", otp_verify_view, name="otp_verify"),
    path("resend-otp/", resend_otp, name="resend_otp"),
]