"""Utility functions for community operations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Community


def community_avatar_path(instance: "Community", filename: str) -> str:
    """
    Generate a custom filepath for community avatars.

    Args:
        instance: The Profile instance
        filename: Original filename

    Returns:
        Path where the avatar should be stored
    """
    ext = filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        ext = "jpg"

    return f"avatars/{instance.name}_avatar.{ext}"
