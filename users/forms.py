from django import forms
from django.forms.widgets import PasswordInput

from users.validators import UserUsernameValidator, validate_user_password


class UserRegisterForm(forms.Form):
    """
    A registration form for creating new user accounts.

    Fields:
        username (CharField): The desired username (max 30 characters).
        email (EmailField): The user's email address (max 250 characters).
        password1 (CharField): The user's chosen password (8-128 characters).
        password2 (CharField): Confirmation of the chosen password (8-128 characters).

    Validation:
        - Ensures that `password1` and `password2` match.
        - Raises a ValidationError with code 'password_mismatch' if they differ.
    """

    username = forms.CharField(
        label="Username",
        max_length=30,
        min_length=3,
        validators=(UserUsernameValidator(),),
    )
    email = forms.EmailField(label="Email", max_length=250)
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        min_length=8,
        max_length=128,
        validators=(validate_user_password,),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        min_length=8,
        max_length=128,
        validators=(validate_user_password,),
    )

    def clean(self) -> dict:
        """
        Ensure that the two password fields match.

        Returns:
            dict: The cleaned form data if validation passes.

        Raises:
            forms.ValidationError: If the two passwords do not match.
        """
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "Passwords do not match.", code="password_mismatch"
            )
        return cleaned_data


class UserLoginForm(forms.Form):
    """
    A secure login form for user authentication.

    This form handles user login with support for both username and email
    authentication.

    Fields:
        username: Accepts either username or email address for flexible login
        password: User's password for authentication
    """

    username = forms.CharField(label="Email/Username", max_length=128)
    password = forms.CharField(
        label="Password", widget=PasswordInput, min_length=8, max_length=128
    )
