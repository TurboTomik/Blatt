"""Custom validators for the Community app models."""

import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class CommunityNameValidator:
    """Validator class for community names with comprehensive validation rules."""

    MIN_LENGTH = 3
    MAX_LENGTH = 30
    PATTERN = r"^[a-z0-9_]+$"

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.min_length = min_length or self.MIN_LENGTH
        self.max_length = max_length or self.MAX_LENGTH

    def __call__(self, value: str) -> None:
        """Call main validator method."""
        if not isinstance(value, str):
            raise ValidationError(
                "Community name must be a string.",
                code="invalid_type",
            )

        # Strip whitespaces
        cleaned_value = value.strip()

        self._validate_length(cleaned_value)
        self._validate_pattern(cleaned_value)
        self._validate_underscores(cleaned_value)

    def _validate_length(self, value: str) -> None:
        """Validate name length."""
        if len(value) < self.min_length:
            raise ValidationError(
                f"Community name must be at least {self.min_length} characters long.",
                code="too_short",
            )

        if len(value) > self.max_length:
            raise ValidationError(
                f"Community name cannot exceed {self.max_length} characters.",
                code="too_long",
            )

    def _validate_pattern(self, value: str) -> None:
        """Validate character pattern."""
        if not re.fullmatch(self.PATTERN, value):
            raise ValidationError(
                "Community name can only contain lowercase English letters (a-z), digits (0-9) and underscores (_).",
                code="invalid_characters",
            )

    def _validate_underscores(self, value: str) -> None:
        """Validate underscore usage rules."""
        if re.search(r"_{2,}", value):
            raise ValidationError(
                "Community name cannot contain consecutive underscores.",
                code="consecutive_underscores",
            )

        if value.startswith("_") or value.endswith("_"):
            raise ValidationError(
                "Community name cannot start or end with an underscore.",
                code="invalid_underscore_position",
            )


@deconstructible
class CommunityDescriptionValidator:
    """Validator class for community descriptions."""

    MAX_LENGTH = 500

    def __init__(self, max_length: int | None = None) -> None:
        self.max_length = max_length or self.MAX_LENGTH

    def __call__(self, value: str) -> None:
        """Call main validator method."""
        # Strip whitespaces
        cleaned_value = value.strip()

        self._validate_length(cleaned_value)

    def _validate_length(self, value: str) -> None:
        """Validate description length."""
        if len(value) > self.max_length:
            raise ValidationError(
                f"Community description cannot exceed {self.max_length} characters.",
                code="too_long",
            )


# Create validator instances
validate_community_name = CommunityNameValidator()
validate_community_description = CommunityDescriptionValidator()
