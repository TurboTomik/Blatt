from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    EmailValidator,
    MaxLengthValidator,
    MinLengthValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone

from .managers import UserManager
from .utils import user_avatar_path
from .validators import UserUsernameValidator, validate_user_password


class User(AbstractUser):
    """
    Enhanced User model with email authentication and additional features.

    This model extends Django's AbstractUser to use email as the primary
    authentication method and adds additional fields and functionality.
    """

    first_name = None
    last_name = None

    email = models.EmailField(
        "email address",
        unique=True,
        validators=[
            EmailValidator(),
        ],
        error_messages={
            "invalid": "Enter a valid email address.",
            "unique": "A user with that email already exists.",
        },
        help_text="Required. Your email address will be verified.",
    )

    username = models.CharField(
        "username",
        max_length=30,
        unique=True,
        validators=[
            UserUsernameValidator(),
        ],
        error_messages={
            "unique": "A user with that username already exists.",
        },
        help_text="Required. 3-30 characters. Letters, numbers and underscores.",
    )

    password = models.CharField(
        "password",
        max_length=128,
        validators=[validate_user_password],
        null=True,
        blank=True,
    )

    email_verified = models.BooleanField(
        "email verified",
        default=False,
        help_text="Designates whether this user has verified their email address.",
    )

    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Token for email verification.",
    )

    email_verification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the verification email was last sent.",
    )

    last_active = models.DateTimeField(
        "last active",
        blank=True,
        null=True,
        help_text="When the user was last active on the site.",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def get_display_name(self) -> None:
        """Return the user's display name (from profile) or username."""
        try:
            if self.profile.display_name:
                return self.profile.display_name
        except (Profile.DoesNotExist, AttributeError):
            pass

        return self.username

    def update_last_active(self) -> None:
        """Update the last_active timestamp to now."""
        self.last_active = timezone.now()
        self.save(update_fields=["last_active"])

    def is_online(self) -> bool:
        """Check if the user is currently online (active in the last 15 minutes)."""
        if not self.last_active:
            return False

        return timezone.now() - self.last_active < timedelta(minutes=15)

    def generate_verification_token(self) -> str:
        """
        Generate and save a new email verification token.

        Returns:
            The generated token
        """
        import secrets

        token = secrets.token_urlsafe(48)
        self.email_verification_token = token
        self.email_verification_sent_at = timezone.now()
        self.save(
            update_fields=["email_verification_token", "email_verification_sent_at"]
        )

        return token

    def verify_email(self, token: str) -> bool:
        """
        Verify the user's email with the provided token.

        Args:
            token: The verification token to check

        Returns:
            True if verification was successful, False otherwise
        """
        if not self.email_verification_token or self.email_verification_token != token:
            return False

        if (
            not self.email_verification_sent_at
            or timezone.now() - self.email_verification_sent_at > timedelta(hours=48)
        ):
            return False

        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save(
            update_fields=[
                "email_verified",
                "email_verification_token",
                "email_verification_sent_at",
            ]
        )

        return True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure that an email is always stored in lowercase."""
        if self.email:
            self.email = self.email.lower()

        if self.username:
            self.username = self.username.strip()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"User: {self.username}"

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["last_active"]),
        ]


class Profile(models.Model):
    """Profile model that holds additional information about a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        primary_key=True,
        verbose_name="user",
    )

    display_name = models.CharField(
        "display_name",
        max_length=30,
        blank=True,
        help_text="Your preferred display name (optional).",
    )

    bio = models.TextField(
        "biography",
        blank=True,
        default="",
        max_length=500,
        validators=[
            MaxLengthValidator(500, "The Bio cannot be longer than 500 characters.")
        ],
        help_text="Tell us about yourself (max 500 characters).",
    )

    location = models.CharField(
        "location",
        max_length=100,
        blank=True,
        help_text="Where you're based (optional).",
    )

    website = models.URLField(
        "website",
        blank=True,
        help_text="Your website or blog (optional).",
    )

    avatar = models.ImageField(
        "avatar",
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        help_text="Upload a profile picture (max 2MB, square image recommended).",
    )

    x = models.CharField(
        "X username", max_length=50, blank=True, help_text="Your X username (optional)."
    )

    github = models.CharField(
        "GitHub username",
        max_length=50,
        blank=True,
        help_text="Your GitHub username (optional).",
    )

    linkedin = models.CharField(
        "LinkedIn username",
        max_length=50,
        blank=True,
        help_text="Your LinkedIn username (optional).",
    )

    created_at = models.DateTimeField(
        "created_at",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "updated_at",
        auto_now=True,
    )

    class Meta:
        db_table = "user_profile"
        verbose_name = "user profile"
        verbose_name_plural = "user profiles"

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"

    def get_avatar_url(self) -> str:
        """
        Get the URL for the user's avatar or a default avatar.

        Returns:
            URL to the avatar image
        """
        if self.avatar and self.avatar.url:
            return self.avatar.url

        return settings.DEFAULT_AVATAR_URL

    def get_social_links(self) -> dict:
        """
        Get a dictionary of the user's social media links.

        Returns:
            Dictionary of social media platform names and URLs
        """
        links = {}

        if self.x:
            links["x"] = f"https://x.com/{self.x}"

        if self.github:
            links["github"] = f"https://github.com/{self.github}"

        if self.linkedin:
            links["linkedin"] = f"https://linkedin.com/in/{self.linkedin}"

        if self.website:
            links["website"] = self.website

        return links


class UserPreferences(models.Model):
    """User preferences for site settings and notifications."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
        primary_key=True,
        verbose_name="user",
    )

    theme = models.CharField(
        "theme",
        max_length=20,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
            ("system", "System"),
        ],
        default="system",
        help_text="Site theme preferences.",
    )

    language = models.CharField(
        "language",
        max_length=20,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text="Preferred language.",
    )

    show_online_status = models.BooleanField(
        "show_online_status",
        default=True,
        help_text="Show when you're online to other users.",
    )

    show_email = models.BooleanField(
        "show email", default=False, help_text="Show when you're online to other users."
    )

    updated_at = models.DateTimeField(
        "updated at",
        auto_now=True,
    )

    class Meta:
        db_table = "user_preferences"
        verbose_name = "user preferences"
        verbose_name_plural = "user preferences"

    def __str__(self) -> str:
        return f"{self.user.username}'s preferences"
