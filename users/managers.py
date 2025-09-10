from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager

if TYPE_CHECKING:
    from .models import User


class UserManager(BaseUserManager):
    """Custom manager for the User model that handles user creation and superuser creation."""

    def create_user(
        self,
        email: str,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and return a regular user with the given email, username, and password.

        Args:
            email: User's email address (required, will be normalized)
            username: User's username (required)
            password: User's password (optional)
            **extra_fields: Additional fields to set on the user

        Returns:
            User: Newly created user instance

        Raises:
            ValueError: If email or username is not provided
        """
        email = self.normalize_email(email)
        username = username.strip()

        user = self.model(
            email=email,
            username=username,
            password=password,
            **extra_fields,
        )
        user.full_clean()
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Create and return a superuser with the given email, username, and password.

        Args:
            email: User's email address (required, will be normalized)
            username: User's username (required)
            password: User's password (optional)
            **extra_fields: Additional fields to set on the user

        Returns:
            User: Newly created superuser instance

        Raises:
            ValueError: If staff or superuser status is explicitly set to False
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, username, password, **extra_fields)
