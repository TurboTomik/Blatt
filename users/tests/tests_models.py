import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from PIL import Image

from users.models import Profile, UserPreferences
from users.utils import user_avatar_path
from users.validators import validate_user_password

User = get_user_model()


@pytest.fixture
def user():
    """Fixture to create a user instance."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="Password!123",
    )


@pytest.fixture
def another_user():
    """Fixture to create another user instance."""
    return User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="Password!123",
    )


@pytest.fixture
def profile(user):
    """Fixture to return a profile instance."""
    return user.profile


@pytest.fixture
def preferences(user):
    """Fixture to return a user preferences instance."""
    return user.preferences


class TestUserModel:
    """Test cases for the User model."""

    @pytest.mark.django_db
    def test_user_creation_with_valid_data(self, user):
        """Test creating a user with valid data."""
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("Password!123")
        assert user.first_name is None
        assert user.last_name is None
        assert not user.email_verified
        assert user.email_verification_token is None
        assert user.email_verification_sent_at is None
        assert user.last_active is None

    @pytest.mark.django_db
    def test_user_string_representation(self, user):
        """Test the __str__ method of User model."""
        expected_str = f"User: {user.username}"
        assert str(user) == expected_str

    @pytest.mark.django_db
    def test_email_field_required(self):
        """Test that email field is required."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                username="testuser",
                email="",  # Empty email should fail
                password="Testpass!123",
            ).full_clean()

    @pytest.mark.django_db
    def test_username_field_required(self):
        """Test that username field is required."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                username="",  # Empty username should fail
                email="test@example.com",
                password="Testpass!123",
            ).full_clean()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "valid_username", ["user_name", "i_am_human", "mr_mann99", "1_duck_1"]
    )
    def test_valid_username(self, valid_username):
        """Test that valid username allowed."""
        User.objects.create_user(
            username=valid_username, email="test@example.com", password="Testpass.123"
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "invalid_username", ["user__name", "I_am_Human", "mr_mann!99", "|duck|"]
    )
    def test_invalid_username(self, invalid_username):
        """Test that valid username allowed."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                username=invalid_username,
                email="test@example.com",
                password="Testpass.123",
            )

    @pytest.mark.django_db
    def test_email_uniqueness(self, user):
        """Test that email must be unique."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="testuser2",
                email="TeSt@exAmple.com",  # Same email
                password="Testpass!123",
            )

    @pytest.mark.django_db
    def test_username_uniqueness(self, user):
        """Test that username must be unique."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                username="testuser",  # Same username
                email="test2@example.com",
                password="Testpass!123",
            )

    @pytest.mark.django_db
    def test_username_max_length(self):
        """Test username max length constraint."""
        long_username = "a" * 31  # 31 characters, should exceed max_length=30

        with pytest.raises(ValidationError):
            User.objects.create_user(
                username=long_username,
                email="test@example.com",
                password="Testpass!123",
            )

    @pytest.mark.django_db
    def test_email_validation(self):
        """Test email field validation."""
        user = User(
            username="testuser",
            email="invalid-email@.com",
            password="Testpass!123",
        )
        with pytest.raises(ValidationError):
            user.full_clean()

    @pytest.mark.django_db
    def test_user_db_table(self):
        """Test that the correct database table is used."""
        assert User._meta.db_table == "user"

    @pytest.mark.django_db
    def test_email_lowercase_save(self):
        """Test that email is saved in lowercase."""
        user = User.objects.create_user(
            username="testuser",
            email="TEST@EXAMPLE.COM",
            password="Password!123",
        )
        assert user.email == "test@example.com"

    @pytest.mark.django_db
    def test_username_strip_save(self):
        """Test that username is stripped of whitespace."""
        user = User.objects.create_user(
            username="  testuser  ",
            email="test@example.com",
            password="Password!123",
        )
        assert user.username == "testuser"

    @pytest.mark.django_db
    def test_get_display_name_with_profile_display_name(self, user):
        """Test get_display_name returns profile display_name when available."""
        user.profile.display_name = "Custom Display Name"
        user.profile.save()

        assert user.get_display_name() == "Custom Display Name"

    @pytest.mark.django_db
    def test_get_display_name_fallback_to_username(self, user):
        """Test get_display_name falls back to username when no profile display_name."""
        assert user.get_display_name() == "testuser"

    @pytest.mark.django_db
    def test_update_last_active(self, user):
        """Test updating last_active timestamp."""
        assert user.last_active is None

        user.update_last_active()

        assert user.last_active is not None
        assert isinstance(user.last_active, datetime)

    @pytest.mark.django_db
    def test_is_online_no_last_active(self, user):
        """Test is_online returns False when no last_active."""
        assert not user.is_online()

    @pytest.mark.django_db
    def test_is_online_recent_activity(self, user):
        """Test is_online returns True for recent activity."""
        user.last_active = timezone.now() - timedelta(minutes=5)
        user.save()

        assert user.is_online()

    @pytest.mark.django_db
    def test_is_online_old_activity(self, user):
        """Test is_online returns False for old activity."""
        user.last_active = timezone.now() - timedelta(minutes=20)
        user.save()

        assert not user.is_online()

    @pytest.mark.django_db
    def test_generate_verification_token(self, user):
        """Test generating email verification token."""
        token = user.generate_verification_token()

        assert token is not None
        assert len(token) > 0
        assert user.email_verification_token == token
        assert user.email_verification_sent_at is not None

    @pytest.mark.django_db
    def test_verify_email_valid_token(self, user):
        """Test email verification with valid token."""
        token = user.generate_verification_token()

        result = user.verify_email(token)

        assert result is True
        assert user.email_verified is True
        assert user.email_verification_token is None
        assert user.email_verification_sent_at is None

    @pytest.mark.django_db
    def test_verify_email_invalid_token(self, user):
        """Test email verification with invalid token."""
        user.generate_verification_token()

        result = user.verify_email("invalid_token")

        assert result is False
        assert user.email_verified is False

    @pytest.mark.django_db
    def test_verify_email_expired_token(self, user):
        """Test email verification with expired token."""
        token = user.generate_verification_token()
        # Simulate token sent 49 hours ago
        user.email_verification_sent_at = timezone.now() - timedelta(hours=49)
        user.save()

        result = user.verify_email(token)

        assert result is False
        assert user.email_verified is False

    @pytest.mark.django_db
    def test_verify_email_no_token(self, user):
        """Test email verification when no token exists."""
        result = user.verify_email("any_token")

        assert result is False
        assert user.email_verified is False


class TestUserManager:
    """Test cases for the UserManager."""

    @pytest.mark.django_db
    def test_create_user_valid(self):
        """Test creating user with valid data."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="Password!123",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("Password!123")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

    @pytest.mark.django_db
    def test_create_user_no_email(self):
        """Test creating user without email raises ValueError."""
        with pytest.raises(ValidationError, match="This field cannot be blank."):
            User.objects.create_user(
                email="",
                username="testuser",
                password="Password!123",
            )

    @pytest.mark.django_db
    def test_create_user_no_username(self):
        """Test creating user without username raises ValueError."""
        with pytest.raises(ValidationError, match="This field cannot be blank."):
            User.objects.create_user(
                email="test@example.com",
                username="",
                password="Password!123",
            )

    @pytest.mark.django_db
    def test_create_user_invalid_password(self):
        """Test creating user with invalid password raises ValidationError."""
        with pytest.raises(ValidationError):
            User.objects.create_user(
                email="test@example.com",
                username="testuser",
                password="weak",
            )

    @pytest.mark.django_db
    def test_create_user_no_password(self):
        """Test creating user without password works."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password=None,
        )

        assert not user.has_usable_password()

    @pytest.mark.django_db
    def test_create_superuser_valid(self):
        """Test creating superuser with valid data."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="Password!123",
        )

        assert user.email == "admin@example.com"
        assert user.username == "admin"
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active

    @pytest.mark.django_db
    def test_create_superuser_not_staff(self):
        """Test creating superuser with is_staff=False raises ValueError."""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                username="admin",
                password="Password!123",
                is_staff=False,
            )

    @pytest.mark.django_db
    def test_create_superuser_not_superuser(self):
        """Test creating superuser with is_superuser=False raises ValueError."""
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                username="admin",
                password="Password!123",
                is_superuser=False,
            )


class TestProfileModel:
    """Test cases for the Profile model."""

    @pytest.mark.django_db
    def test_profile_creation(self, profile, user):
        """Test creating a profile."""
        assert profile.user == user
        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.location == ""
        assert profile.website == ""
        assert not profile.avatar
        assert profile.x == ""
        assert profile.github == ""
        assert profile.linkedin == ""

    @pytest.mark.django_db
    def test_profile_string_representation(self, profile, user):
        """Test the __str__ method of Profile model."""
        expected_str = f"{user.username}'s profile"
        assert str(profile) == expected_str

    @pytest.mark.django_db
    def test_profile_bio_can_be_blank(self, profile):
        """Test that bio can be blank."""
        profile.bio = ""
        profile.full_clean()
        assert profile.bio == ""

    @pytest.mark.django_db
    def test_profile_one_to_one_relationship(self, profile, user):
        """Test OneToOneField relationship with User."""
        # Test forward relationship
        assert profile.user == user
        # Test reverse relationship
        assert user.profile == profile

    @pytest.mark.django_db
    def test_profile_cascade_deletion(self, profile, user):
        """Test that profile is deleted when user is deleted."""
        profile_id = profile.pk
        user.delete()

        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(pk=profile_id)

    @pytest.mark.django_db
    def test_profile_primary_key(self, profile, user):
        """Test that user field is the primary key."""
        assert profile.pk == user.pk

    @pytest.mark.django_db
    def test_profile_unique_constraint(self, profile, user):
        """Test that each user can have only one profile."""
        with pytest.raises(IntegrityError):
            Profile.objects.create(user=user, bio="Second profile")

    @pytest.mark.django_db
    def test_profile_avatar_field(self, profile, user):
        """Test avatar ImageField."""
        # Create a simple test image
        image = Image.new("RGB", (100, 100), color="red")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file.name)
            temp_file_path = temp_file.name

        try:
            with Path.open(temp_file_path, "rb") as f:
                uploaded_file = SimpleUploadedFile(
                    name="test_avatar.jpg",
                    content=f.read(),
                    content_type="image/jpeg",
                )

                profile.avatar = uploaded_file
                profile.save()

                assert profile.avatar
                assert profile.avatar.name.startswith("avatars/")
        finally:
            # Clean up temp file
            Path.unlink(temp_file_path)
            if profile.avatar:
                try:  # noqa: SIM105
                    Path.unlink(f"media/{profile.avatar.name}")
                except FileNotFoundError:
                    pass

    @pytest.mark.django_db
    def test_profile_db_table(self):
        """Test that the correct database table is used."""
        assert Profile._meta.db_table == "user_profile"

    @pytest.mark.django_db
    def test_get_avatar_url_no_avatar(self, profile):
        """Test get_avatar_url returns default when no avatar."""
        url = profile.avatar_url
        assert url == "/static/img/default_avatar.jpg"

    @pytest.mark.django_db
    def test_get_avatar_url_with_avatar(self, profile):
        """Test get_avatar_url returns avatar URL when avatar exists."""
        profile.avatar.name = "avatars/test.jpg"

        with patch.object(
            profile.avatar.storage, "url", return_value="/media/" + profile.avatar.name
        ):
            url = profile.avatar_url
            assert url == "/media/avatars/test.jpg"

    @pytest.mark.django_db
    def test_get_social_links_empty(self, profile):
        """Test get_social_links returns empty dict when no links."""
        links = profile.get_social_links()
        assert links == {}

    @pytest.mark.django_db
    def test_get_social_links_with_data(self, profile):
        """Test get_social_links returns correct links when data exists."""
        profile.x = "testuser"
        profile.github = "testuser"
        profile.linkedin = "testuser"
        profile.website = "https://testuser.com"
        profile.save()

        links = profile.get_social_links()

        expected = {
            "x": "https://x.com/testuser",
            "github": "https://github.com/testuser",
            "linkedin": "https://linkedin.com/in/testuser",
            "website": "https://testuser.com",
        }
        assert links == expected


class TestUserPreferencesModel:
    """Test cases for the UserPreferences model."""

    @pytest.mark.django_db
    def test_preferences_creation(self, preferences, user):
        """Test creating user preferences."""
        assert preferences.user == user
        assert preferences.theme == "system"
        assert preferences.language == "en-us"
        assert preferences.show_online_status is True
        assert preferences.show_email is False

    @pytest.mark.django_db
    def test_preferences_string_representation(self, preferences, user):
        """Test the __str__ method of UserPreferences model."""
        expected_str = f"{user.username}'s preferences"
        assert str(preferences) == expected_str

    @pytest.mark.django_db
    def test_preferences_one_to_one_relationship(self, preferences, user):
        """Test OneToOneField relationship with User."""
        # Test forward relationship
        assert preferences.user == user
        # Test reverse relationship
        assert user.preferences == preferences

    @pytest.mark.django_db
    def test_preferences_cascade_deletion(self, preferences, user):
        """Test that preferences are deleted when user is deleted."""
        preferences_id = preferences.pk
        user.delete()
        with pytest.raises(UserPreferences.DoesNotExist):
            UserPreferences.objects.get(pk=preferences_id)

    @pytest.mark.django_db
    def test_preferences_primary_key(self, preferences, user):
        """Test that user field is the primary key."""
        assert preferences.pk == user.pk

    @pytest.mark.django_db
    def test_preferences_unique_constraint(self, preferences, user):
        """Test that each user can have only one preferences object."""
        # Try to create second preferences for same user
        with pytest.raises(IntegrityError):
            UserPreferences.objects.create(user=user, theme="dark")

    @pytest.mark.django_db
    def test_preferences_theme_choices(self, preferences):
        """Test theme field choices."""
        for theme in ["light", "dark", "system"]:
            preferences.theme = theme
            preferences.full_clean()

    @pytest.mark.django_db
    def test_preferences_db_table(self):
        """Test that the correct database table is used."""
        assert UserPreferences._meta.db_table == "user_preferences"


class TestUserPasswordValidator:
    """Test cases for the UserPasswordValidator."""

    @pytest.mark.parametrize(
        "valid_password",
        [
            "Password!123",
            "MySecure@Pass1",
            "Complex#Pass123",
            "Strong$Password1",
            "Test&Password123",
        ],
    )
    def test_valid_passwords(self, valid_password):
        """Test that valid passwords pass validation."""
        validate_user_password(valid_password)

    @pytest.mark.parametrize(
        "invalid_password,expected_error",
        [
            ("short", "too_short"),
            ("password123", "invalid_characters"),
            ("PASSWORD123", "invalid_characters"),
            ("Password!", "invalid_characters"),
            ("Password123", "invalid_characters"),
            ("a" * 121, "too_long"),
        ],
    )
    def test_invalid_passwords(self, invalid_password, expected_error):
        """Test that invalid passwords fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_user_password(invalid_password)
        assert expected_error in str(exc_info.value.code)

    def test_non_string_password(self):
        """Test that non-string input raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_user_password(12345)


class TestSignals:
    """Test cases for signal handlers."""

    @pytest.mark.django_db
    def test_profile_created_on_user_creation(self):
        """Test that Profile is created automatically when User is created."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Password!123",
        )

        # Profile should exist
        assert hasattr(user, "profile")
        assert user.profile is not None
        assert isinstance(user.profile, Profile)

    @pytest.mark.django_db
    def test_preferences_created_on_user_creation(self):
        """Test that UserPreferences is created automatically when User is created."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Password!123",
        )

        # Preferences should exist
        assert hasattr(user, "preferences")
        assert user.preferences is not None
        assert isinstance(user.preferences, UserPreferences)

    @pytest.mark.django_db
    def test_signal_not_triggered_on_update(self, user):
        """Test that signals are not triggered when updating existing user."""
        original_profile = user.profile
        original_preferences = user.preferences

        # Update user
        user.email = "updated@example.com"
        user.save()

        # Same instances should still exist
        assert user.profile == original_profile
        assert user.preferences == original_preferences


class TestUtils:
    """Test cases for utility functions."""

    @pytest.mark.django_db
    def test_user_avatar_path(self, user):
        """Test user_avatar_path function."""
        # Mock profile instance
        profile = user.profile
        filename = "test_avatar.jpg"

        path = user_avatar_path(profile, filename)

        # Should start with avatars/
        assert path.startswith("avatars/")
        # Should contain user ID
        assert f"user_{user.id}" in path
        # Should end with correct extension
        assert path.endswith(".jpg")

    @pytest.mark.django_db
    def test_user_avatar_path_different_extensions(self, user):
        """Test user_avatar_path with different file extensions."""
        profile = user.profile

        test_cases = [
            ("test.png", ".png"),
            ("test.jpeg", ".jpeg"),
            ("test.gif", ".gif"),
            ("test.webp", ".webp"),
            ("test.invalid", ".jpg"),  # Invalid extension defaults to jpg
        ]

        for filename, expected_ext in test_cases:
            path = user_avatar_path(profile, filename)
            assert path.endswith(expected_ext)


class TestModelIntegration:
    """Test integration between User, Profile, and UserPreferences models."""

    @pytest.mark.django_db
    def test_user_profile_preferences_relationship(self, user):
        """Test the relationship between User, Profile, and UserPreferences."""
        # Test that user can access profile
        assert user.profile is not None
        assert user.profile.user == user

        # Test that user can access preferences
        assert user.preferences is not None
        assert user.preferences.user == user

        # Test that profile and preferences are different objects
        assert user.profile != user.preferences


class TestEdgeCases:
    """Test edge cases and potential issues."""

    @pytest.mark.django_db
    def test_unicode_characters_in_bio(self, profile):
        """Test bio with unicode characters."""
        unicode_bio = "Testing unicode: 你好世界 🌍 café naïve"
        profile.bio = unicode_bio
        profile.save()

        assert profile.bio == unicode_bio

    @pytest.mark.django_db
    def test_very_long_bio(self, profile):
        """Test bio with maximum allowed length."""
        max_bio = "a" * 500
        profile.bio = max_bio
        profile.full_clean()  # Should not raise

        assert len(profile.bio) == 500

    @pytest.mark.django_db
    def test_bio_exceeds_max_length(self, profile):
        """Test bio exceeding maximum length fails validation."""
        too_long_bio = "a" * 501
        profile.bio = too_long_bio

        with pytest.raises(ValidationError):
            profile.full_clean()


class TestPostgreSQLSpecific:
    """Tests specific to PostgreSQL database features."""

    @pytest.mark.django_db
    def test_email_case_insensitivity(self):
        """Test email case insensitivity."""
        User.objects.create_user(
            username="user1",
            email="Test@Example.com",
            password="Testpass!123",
        )

        # This shouldn't work as emails are case-insensitive
        with (
            pytest.raises(
                ValidationError, match="A user with that email already exists."
            ),
            transaction.atomic(),
        ):
            User.objects.create_user(
                username="user2",
                email="test@example.com",
                password="Password!123",
            )

        assert User.objects.filter(email__iexact="test@example.com").count() == 1

    @pytest.mark.django_db
    def test_unicode_support(self, profile):
        """Test PostgreSQL unicode support."""
        profile.bio = "Unicode test: 你好世界 🌍 café naïve résumé"
        profile.save()

        # Retrieve from database and verify unicode is preserved
        retrieved_profile = Profile.objects.get(user=profile.user)
        assert retrieved_profile.bio == "Unicode test: 你好世界 🌍 café naïve résumé"

    @pytest.mark.django_db
    def test_large_text_fields(self, profile):
        """Test handling of large text in PostgreSQL."""
        # Create a large bio (PostgreSQL TEXT field can handle this)
        large_bio = "A" * 500  # Max allowed length
        profile.bio = large_bio
        profile.save()

        retrieved_profile = Profile.objects.get(user=profile.user)
        assert len(retrieved_profile.bio) == 500

    @pytest.mark.django_db
    def test_database_constraints_with_null_values(self, profile):
        """Test database behavior with null values."""
        # Profile with null avatar should work
        profile.avatar = None
        profile.save()

        assert profile.avatar.name is None

    @pytest.mark.django_db(transaction=True)
    def test_transaction_rollback(self, user):
        """Test that transactions rollback properly on errors."""
        original_bio = user.profile.bio

        # This should rollback and not change the profile
        try:
            with transaction.atomic():
                user.profile.bio = "Test"
                user.profile.save()
                # Create duplicate profile to trigger error
                Profile.objects.create(user=user, bio="Duplicate")
        except IntegrityError:
            pass

        # Profile bio should be unchanged due to rollback
        user.profile.refresh_from_db()
        assert user.profile.bio == original_bio
