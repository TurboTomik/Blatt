"""Utility functions for user-related operations."""

import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Profile


def user_avatar_path(instance: "Profile", filename: str) -> str:
    """
    Generate a custom file path for user avatars.

    Args:
        instance: The Profile instance
        filename: Original filename

    Returns:
        Path where the avatar should be stored
    """
    ext = filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        ext = "jpg"

    random_str = secrets.token_urlsafe(8)
    return f"avatars/user_{instance.user.id}_{random_str}.{ext}"
