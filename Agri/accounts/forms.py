from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(forms.Form):
    contact_number = forms.CharField(label="Mobile Number")
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label="Role"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Password"
    )
    use_otp = forms.BooleanField(
        required=False,
        label="Login with OTP"
    )
