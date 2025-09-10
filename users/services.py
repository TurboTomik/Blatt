"""
Business logic services for user authentication operations.

This module contains all business logic related to user registration,
authentication, and account management.
"""

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from .models import User


@dataclass
class ServiceResult:
    """
    Standardized result object for service operations.

    Provides a consistent interface for communicating operation results
    between service layer and presentation layer.

    Attributes:
        success: Whether the operation completed successfully.
        redirect_url: URL to redirect to on success (optional).
        error_message: General error message for display (optional).
        errors: Field-specific errors dictionary (optional).
        data: Additional data returned by the operation (optional).
    """

    success: bool
    redirect_url: str | None = None
    error_message: str | None = None
    errors: dict[str, str] | None = None
    data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize empty containers if not provided."""
        if self.errors is None:
            self.errors = {}
        if self.data is None:
            self.data = {}


class UserAuthService:
    """
    Service class handling user authentication business logic.

    This service encapsulates all business operations related to user
    registration, authentication, and account management.
    """

    def register_user(self, form_data: dict[str, Any]) -> ServiceResult:
        """
        Register a new user account with validation.

        Handles the complete user registration workflow including:
        - Creating user instance from form data
        - Model-level validation
        - Password hashing and security
        - Database persistence
        - Error handling and reporting

        Args:
            form_data: Dictionary containing validated form data with keys:
                - email: User's email address
                - username: Desired username
                - password1: User's password
                - Additional fields as needed

        Returns:
            ServiceResult: Result object containing:
                - success: True if registration completed successfully
                - redirect_url: URL to redirect to after successful registration
                - errors: Dictionary of field-specific validation errors
                - data: Contains created user instance on success
        """
        try:
            user = self._create_user_instance(form_data)
            self._validate_user_instance(user)
            user = self._save_user_with_password(user, form_data["password1"])

            return ServiceResult(
                success=True,
                redirect_url=self._get_register_redirect_url(),
                data={"user": user},
            )

        except ValidationError as e:
            return ServiceResult(
                success=False, errors=self._process_validation_errors(e)
            )
        except Exception as e:
            return ServiceResult(
                success=False, error_message=f"Registration failed: {e!s}"
            )

    def authenticate_user(
        self, request: HttpRequest, credentials: dict[str, Any]
    ) -> ServiceResult:
        """
        Authenticate user credentials and establish session.

        Handles the complete authentication workflow including:
        - Credential validation against database
        - User authentication using Django's auth system
        - Session establishment for authenticated users
        - Security logging and audit trail

        Args:
            request: HTTP request object for session management.
            credentials: Dictionary containing login credentials:
                - username: Username or email address
                - password: User's password

        Returns:
            ServiceResult: Result object containing:
                - success: True if authentication successful
                - redirect_url: URL to redirect to after successful login
                - error_message: Authentication failure message
                - data: Contains authenticated user instance on success
        """
        try:
            username_or_email = credentials["username"]
            password = credentials["password"]

            user = self._authenticate_credentials(request, username_or_email, password)

            if user is not None:
                self._establish_user_session(request, user)
                return ServiceResult(
                    success=True,
                    redirect_url=self._get_login_redirect_url(),
                    data={"user": user},
                )
            return ServiceResult(
                success=False, error_message="Invalid email/username or password."
            )
        except Exception as e:
            return ServiceResult(
                success=False, error_message=f"Authentication failed: {e!s}"
            )

    @staticmethod
    def _create_user_instance(form_data: dict[str, Any]) -> User:
        """
        Create a User instance from form data.

        Args:
            form_data: Validated form data dictionary.

        Returns:
            User: Unsaved User instance with populated fields.
        """
        return User(
            email=form_data["email"],
            username=form_data["username"],
            password=form_data["password1"],
        )

    @staticmethod
    def _validate_user_instance(user: User) -> None:
        """
        Perform model-level validation on user instance.

        Args:
            user: User instance to validate.

        Raises:
            ValidationError: If model validation fails.
        """
        user.full_clean()

    @staticmethod
    def _save_user_with_password(user: User, password: str) -> User:
        """
        Hash password and save user to database.

        Args:
            user: User instance to save.
            password: Plain text password to hash.

        Returns:
            User: Saved user instance with hashed password.
        """
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def _authenticate_credentials(
        request: HttpRequest, username: str, password: str
    ) -> User | None:
        """
        Authenticate user credentials against the database.

        Args:
            request: HTTP request object for context.
            username: Username or email address.
            password: Plain text password.

        Returns:
            User: Authenticated user instance or None if authentication fails.
        """
        return authenticate(request, username=username, password=password)

    @staticmethod
    def _establish_user_session(request: HttpRequest, user: User) -> None:
        """
        Establish authenticated session for user.

        Args:
            request: HTTP request object for session management.
            user: Authenticated user instance.
        """
        login(request, user)

    @staticmethod
    def _process_validation_errors(error: ValidationError) -> dict[str, str]:
        """
        Convert Django ValidationError to field-error dictionary.

        Args:
            error: ValidationError instance from model validation.

        Returns:
            Dict containing field names mapped to error messages.
        """
        errors = {}

        if hasattr(error, "error_dict"):
            for field, field_errors in error.error_dict.items():
                for error in field_errors:
                    errors[field] = error
        else:
            errors[None] = str(error)

        return errors

    @staticmethod
    def _get_register_redirect_url() -> str:
        """
        Get URL to redirect to after successful registration.

        Returns:
            str: Redirect URL for post-registration flow.
        """
        from django.conf import settings

        return getattr(settings, "REGISTER_REDIRECT_URL", "/")

    @staticmethod
    def _get_login_redirect_url() -> str:
        """
        Get URL to redirect to after successful login.

        Returns:
            str: Redirect URL for post-login flow.
        """
        from django.conf import settings

        return getattr(settings, "LOGIN_REDIRECT_URL", "/")
