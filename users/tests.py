import os
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.utils import DataError
from PIL import Image

from .models import Profile

User = get_user_model()


@pytest.fixture
def user():
    """Fixture to create a user instance."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="password123"
    )


@pytest.fixture
def profile(user):
    """Fixture to return a profile instance."""
    return user.profile


class TestUserModel:
    """Test cases for the User model"""

    @pytest.mark.django_db
    def test_user_creation_with_valid_data(self, user):
        """Test creating a user with valid data"""
        assert user.username == "testuser"
        assert user.email, "test@example.com"
        assert user.check_password("password123")
        assert user.first_name is None
        assert user.last_name is None

    @pytest.mark.django_db
    def test_user_string_representation(self, user):
        """Test the __str__ method of User model"""
        expected_str = f"User: {user.username}"
        assert str(user) == expected_str

    @pytest.mark.django_db
    def test_email_field_required(self):
        """Test that email field is required"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username="testuser",
                email="",  # Empty email should fail
                password="testpass123",
            ).full_clean()

    @pytest.mark.django_db
    def test_username_field_required(self):
        """Test that username field is required"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username="",  # Empty username should fail
                email="test@example.com",
                password="testpass123",
            ).full_clean()

    @pytest.mark.django_db
    def test_email_uniqueness(self, user):
        """Test that email must be unique"""

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="testuser2",
                email="TeSt@exAmple.com",  # Same email
                password="testpass123",
            )

    @pytest.mark.django_db
    def test_username_uniqueness(self, user):
        """Test that username must be unique"""

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="testuser",  # Same username
                email="test2@example.com",
                password="testpass123",
            )

    @pytest.mark.django_db
    def test_username_max_length(self):
        """Test username max length constraint"""
        long_username = "a" * 31  # 31 characters, should exceed max_length=30

        with pytest.raises(DataError):
            User.objects.create_user(
                username=long_username,
                email="test@example.com",
                password="testpass123",
            )

    @pytest.mark.django_db
    def test_email_validation(self):
        """Test email field validation"""
        user = User(
            username="testuser", email="invalid-email@.com", password="testpass123"
        )

        with pytest.raises(ValidationError):
            user.full_clean()

    @pytest.mark.django_db
    def test_user_db_table(self):
        """Test that the correct database table is used"""
        assert User._meta.db_table == "user"


class TestProfileModel:
    """Test cases for the Profile model"""

    @pytest.mark.django_db
    def test_profile_creation(self, profile, user):
        """Test creating a profile"""
        assert profile.user == user
        assert profile.bio == ""
        assert not profile.avatar

    @pytest.mark.django_db
    def test_profile_string_representation(self, profile, user):
        """Test the __str__ method of Profile model"""
        expected_str = f"{user.username}'s profile"

        assert str(profile) == expected_str

    @pytest.mark.django_db
    def test_profile_bio_can_be_blank(self, profile):
        """Test that bio can be blank"""
        profile.bio = ""
        profile.full_clean()  # Should not raise validation error

        assert profile.bio == ""

    @pytest.mark.django_db
    def test_profile_one_to_one_relationship(self, profile, user):
        """Test OneToOneField relationship with User"""

        # Test forward relationship
        assert profile.user == user

        # Test reverse relationship
        assert user.profile == profile

    @pytest.mark.django_db
    def test_profile_cascade_deletion(self, profile, user):
        """Test that profile is deleted when user is deleted"""
        profile_id = profile.pk

        user.delete()

        # Profile should be deleted too
        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(pk=profile_id)

    @pytest.mark.django_db
    def test_profile_primary_key(self, profile, user):
        """Test that user field is the primary key"""
        assert profile.pk, user.pk

    @pytest.mark.django_db
    def test_profile_unique_constraint(self, profile, user):
        """Test that each user can have only one profile"""

        # Try to create second profile for same user
        with pytest.raises(IntegrityError):
            Profile.objects.create(user=user, bio="Second profile")

    @pytest.mark.django_db
    def test_profile_avatar_field(self, profile, user):
        """Test avatar ImageField"""
        # Create a simple test image
        image = Image.new("RGB", (100, 100), color="red")
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(temp_file.name)
        temp_file.close()

        try:
            with open(temp_file.name, "rb") as f:
                uploaded_file = SimpleUploadedFile(
                    name="test_avatar.jpg", content=f.read(), content_type="image/jpeg"
                )

                profile.avatar = uploaded_file
                profile.save()

                assert profile.avatar
                assert profile.avatar.name.startswith("avatars/")
        finally:
            # Clean up temp file
            os.unlink(temp_file.name)
            os.unlink(f"media/{profile.avatar.name}")

    @pytest.mark.django_db
    def test_profile_db_table(self):
        """Test that the correct database table is used"""
        assert Profile._meta.db_table == "user_profile"


class TestModelIntegration:
    """Test integration between User and Profile model"""

    @pytest.mark.django_db
    def test_user_profile_relationship(self, profile, user):
        """Test the relationship between User and Profile"""

        # Test that user can access profile
        assert user.profile == profile

        # Test that profile can access user
        assert profile.user == user


class TestEdgeCases:
    """Test edge cases and potential issues"""

    @pytest.mark.django_db
    def test_user_with_special_characters_in_username(self):
        """Test username with special characters"""
        user = User.objects.create_user(
            username="test.user_123", email="test@example.com", password="testpass123"
        )

        user.full_clean()
        assert user.username == "test.user_123"

    @pytest.mark.django_db
    def test_unicode_characters_in_bio(self, profile, user):
        """Test bio with unicode characters"""
        unicode_bio = "Testing unicode: 你好世界 🌍 café naïve"
        profile.bio = unicode_bio

        assert profile.bio == unicode_bio


class TestPostgreSQLSpecific:
    """Tests specific to PostgreSQL database features"""

    @pytest.mark.django_db
    def test_case_sensitive_usernames(self):
        """Test that PostgreSQL treats usernames as case-sensitive"""
        User.objects.create_user(
            username="TestUser", email="test1@example.com", password="testpass123"
        )

        # This should work as PostgreSQL is case-sensitive
        User.objects.create_user(
            username="testuser", email="test2@example.com", password="testpass123"
        )

        assert User.objects.filter(username__iexact="testuser").count() == 2

    @pytest.mark.django_db
    def test_email_case_insensitivity(self):
        """Test email case insensitivity"""
        User.objects.create_user(
            username="user1", email="Test@Example.com", password="testpass123"
        )

        # This shouldn't work as emails are case-insensitive
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="user2", email="test@example.com", password="testpass123"
                )

        assert User.objects.filter(email__iexact="test@example.com").count() == 1

    @pytest.mark.django_db
    def test_unicode_support(self, profile, user):
        """Test PostgreSQL unicode support"""
        user.profile.bio = "Unicode test: 你好世界 🌍 café naïve résumé"
        profile.save()

        # Retrieve from database and verify unicode is preserved
        retrieved_profile = Profile.objects.get(user=user)
        assert retrieved_profile.bio == "Unicode test: 你好世界 🌍 café naïve résumé"

    @pytest.mark.django_db
    def test_large_text_fields(self, profile, user):
        """Test handling of large text in PostgreSQL"""

        # Create a very large bio (PostgreSQL TEXT field can handle this)
        large_bio = "A" * 100000  # 100KB of text
        user.profile.bio = large_bio
        profile.save()

        retrieved_profile = Profile.objects.get(user=user)
        assert len(retrieved_profile.bio) == 100000

    @pytest.mark.django_db
    def test_database_constraints_with_null_values(self, profile, user):
        """Test database behavior with null values"""
        # Profile with null avatar should work
        profile.avatar = None

        assert profile.avatar.name is None

    @pytest.mark.django_db(transaction=True)
    def test_transaction_rollback(self, user):
        """Test that transactions rollback properly on errors"""
        # This should rollback and not create a profile
        try:
            with transaction.atomic():
                Profile.objects.create(user=user, bio="Test")
                # Create duplicate profile to trigger error
                Profile.objects.create(user=user, bio="Duplicate")
        except IntegrityError:
            pass

        # Profile should not exist due to rollback
        assert Profile.objects.get(user=user).bio == ""
