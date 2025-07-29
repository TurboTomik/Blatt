from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserManager(BaseUserManager):
    """Custom manager for the User model that handles user creation and superuser creation."""

    def create_user(
        self,
        email: str,
        username: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Create and return a regular user with the given email, username, and password."""
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
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
        """Create and return a superuser with the given email, username, and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Custom User model."""

    first_name = None
    last_name = None
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, **kwargs: Any) -> None:
        """Override save to ensure that an email is always stored in lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(**kwargs)

    def __str__(self) -> str:
        return f"User: {self.username}"

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"


def user_avatar_path(instance: "Profile", filename: str) -> str:
    """Generate custom file path for user avatars."""
    return f"avatars/user_{instance.user.id}.{filename.split('.')[-1]}"


class Profile(models.Model):
    """Profile model that holds additional information about a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        primary_key=True,
    )
    bio = models.TextField(
        "biography",
        blank=True,
        default="",
        max_length=500,
        help_text="Tell us about yourself (max 500 characters)",
    )
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        help_text="Upload a profile picture",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"


# Signals to auto-create profiles
@receiver(post_save, sender=User)
def create_user_profile(
    instance: User,
    created: bool,
    *_args: Any,
    **_kwargs: Any,
) -> None:
    """Signal receiver that automatically creates a Profile instance when a new User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(instance: User, *_args: Any, **_kwargs: Any) -> None:
    """Signal receiver that automatically saves the associated Profile instance when a User is saved."""
    instance.profile.save()
