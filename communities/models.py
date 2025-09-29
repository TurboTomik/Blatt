from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.forms import ValidationError
from django.urls import reverse

from users.models import User

from .validators import validate_community_description, validate_community_name


class CommunityManager(models.Manager):
    """Custom manager for Community model."""

    def create_community(self, name: str, creator: User) -> "Community":
        """
        Create a new community and subscribe the creator.

        Args:
            name (str): The name of the community to create.
            creator (User): The user who is creating the community.

        Returns:
            Community: The newly created community instance.
        """
        community = self.create(name=name, creator=creator)
        Subscription.objects.subscribe_user(community=community, user=creator)
        return community

    def _validate_and_clean_str(
        self,
        value: str,
        field_name: str = "value",
    ) -> str | None:
        """
        Validate that the input is a non-empty string and return the stripped version.

        Args:
            value (str): The string to validate and clean.
            field_name (str): The name of the field, used in error messages.

        Returns:
            str or None: The cleaned (stripped) string if valid, otherwise None.

        Raises:
            TypeError: If 'value' is not a string.
        """
        if not isinstance(value, str):
            raise TypeError(
                f"Expected '{field_name}' to be str, got {type(value).__name__} instead.",
            )

        value = value.strip()
        return value or None

    def get_by_name(self, name: str) -> "Community | None":
        """
        Retrieve a Community by its exact name (case-insensitive).

        Args:
            name (str): The exact name of the community to retrieve.

        Returns:
            Community or None: The matching Community object if found, otherwise None.

        Raises:
            TypeError: If 'name' is not a string.
        """
        if not self._validate_and_clean_str(name, field_name="name"):
            return None

        try:
            return self.get(name__iexact=name)
        except ObjectDoesNotExist:
            return None

    def search_by_name(self, query: str) -> QuerySet["Community"]:
        """
        Search for communities by name pattern (case-insensitive).

        Args:
            query (str): The partial name string to search for.

        Returns:
            QuerySet[Community]: A queryset of matching Community objects.

        Raises:
            TypeError: If 'query' is not a string.
        """
        query = self._validate_and_clean_str(query, field_name="query")
        if query is None:
            return self.none()

        return self.filter(name__icontains=query)


class Community(models.Model):
    """
    Community model represent user communities.

    A community is a group where users can subscribe and participate.
    Community names must follow specific naming conversation.
    """

    name = models.CharField(
        max_length=30,
        unique=True,
        validators=[validate_community_name],
        help_text=(
            "Only English lowercase letters, digits and underscores are allowed. "
            "Must be 3-30 characters long."
        ),
        verbose_name="Community Name",
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        default="",
        validators=[validate_community_description],
        help_text="Optional description up to 500 characters.",
        verbose_name="Community Description",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    creator = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
        related_name="created_communities",
        verbose_name="Creator",
        help_text="User who created this community",
    )

    objects = CommunityManager()

    class Meta:
        db_table = "community"
        ordering = ["name"]
        verbose_name = "Community"
        verbose_name_plural = "Communities"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Community: {self.name}"

    def __repr__(self) -> str:
        return f"<Community(id={self.id}, name='{self.name}')>"

    def save(self, **kwargs: Any) -> None:
        """Override save to ensure validation and normalization."""
        self.full_clean()
        super().save(**kwargs)

    def get_absolute_url(self) -> str:
        """Return the absolute URL of this community instance."""
        return reverse("community-detail", kwargs={"name": self.name})

    def clean(self) -> None:
        """Additional model-level validation."""
        super().clean()

        # Normalize name
        if self.name and isinstance(self.name, str):
            self.name = self.name.strip().lower()

        # Normalize Description
        if self.description and isinstance(self.description, str):
            self.description = self.description.strip()

    @property
    def subscriber_count(self) -> int:
        """
        Get the total number of subscribers for this community.

        Returns:
            int: The count of subscribers (subscriptions).
        """
        return self.subscriptions.count()

    def is_subscribed_by(self, user: User) -> bool:
        """
        Check if the given user is subscribed to this community.

        Args:
            user (User): The user to check for subscription.

        Returns:
            bool: True if the user is subscribed, False otherwise.
        """
        if not user or not user.is_authenticated:
            return False
        return self.subscriptions.filter(user=user).exists()


class SubscriptionManager(models.Manager):
    """Custom manager for Subscription model."""

    def subscribe_user(self, user: User, community: Community) -> bool:
        """
        Subscribe a user to a community.

        Args:
            user (User): The user to be subscribed.
            community (Community): The community the user will be subscribed to.

        Returns:
            tuple: Boolean indicating whether the subscription was created (`True`)
            or already exists (`False`).
        """
        _, created = self.get_or_create(
            user=user,
            community=community,
        )
        return created

    def unsubscribe_user(self, user: User, community: Community) -> bool:
        """
        Unsubscribe a user from a community.

        Args:
            user (User): The user to unsubscribe.
            community (Community): The community to unsubscribe from.

        Returns:
            bool: True if the user was unsubscribed, False if user
            wasn't subscribed before.
        """
        deleted_count, _ = self.filter(user=user, community=community).delete()
        return deleted_count > 0


class Subscription(models.Model):
    """
    Subscription model representing user subscriptions to communities.

    This model creates a many-to-many relationship between users and communities
    with additional metadata like subscription timestamp.
    """

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="User",
    )
    community = models.ForeignKey(
        to=Community,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Community",
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Subscribed At",
    )

    objects = SubscriptionManager()

    class Meta:
        db_table = "subscription"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ["-subscribed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "community"],
                name="unique_user_community_subscription",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "community"]),
            models.Index(fields=["subscribed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} subscribed to {self.community.name}"

    def __repr__(self) -> str:
        return f"<Subscription(user='{self.user.username}', community='{self.community.name}')>"

    def save(self, **kwargs: Any) -> None:
        """Override to ensure validation."""
        self.full_clean()
        super().save(**kwargs)

    def clean(self) -> None:
        """Model-level validation."""
        super().clean()

        if not getattr(self, "user", None):
            raise ValidationError({"user": "User is required for subscription."})
        if not getattr(self, "community", None):
            raise ValidationError(
                {"community": "Community is required for subscription."},
            )
