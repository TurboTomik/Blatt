from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User, UserPreferences


@receiver(post_save, sender=User)
def create_user_related_models(
    sender: Any,
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Signal handler to create related models when a new User is created.

    Args:
        sender: The model class that sent the signal
        instance: The User instance that was saved
        created: Whether the instance was created or updated
        **kwargs: Additional signal arguments
    """
    if created:
        # Create profile
        Profile.objects.get_or_create(user=instance)

        # Create preferences
        UserPreferences.objects.get_or_create(user=instance)
