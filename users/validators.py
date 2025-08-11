import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class UserPasswordValidator:
    """Validator class for user password."""

    MIN_LENGTH = 8
    MAX_LENGTH = 120
    PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,120}$"

    def __init__(
        self, min_length: int | None = None, max_length: int | None = None
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

    def _validate_length(self, value: str) -> None:
        """Validate name length."""
        if len(value) < self.min_length:
            raise ValidationError(
                f"Password must be at least {self.min_length} characters long.",
                code="too_short",
            )

        if len(value) > self.max_length:
            raise ValidationError(
                f"Password cannot exceed {self.max_length} characters.",
                code="too_long",
            )

    def _validate_pattern(self, value: str) -> None:
        """Validate character pattern."""
        if not re.fullmatch(self.PATTERN, value):
            raise ValidationError(
                (
                    "Password must be 8-120 characters long and include at least one "
                    "letter, one number, and one special character "
                    "(!,@,#,$,%,^,&,*,(,),,,.,?,\",:,{,},|,<,>)."
                ),
                code="invalid_characters",
            )


validate_user_password = UserPasswordValidator()
