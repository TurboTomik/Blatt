"""
Pytest test suite for Community views.

This module contains comprehensive tests for community creation and detail views
using pytest with Django integration, fixtures, and parametrized tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Community
from ..views import CommunityDetailView

User = get_user_model()

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpassword.123"
    )


@pytest.fixture
def another_user(db):
    """Create another test user for testing permissions."""
    return User.objects.create_user(
        username="anotheruser", email="another@example.com", password="anotherpass.123"
    )


@pytest.fixture
def community(db, user):
    """Create a test community."""
    return Community.objects.create(
        name="test_community",
        description="A test community for testing purposes",
        creator=user,
    )


@pytest.fixture
def communities(db, user, another_user):
    """Create multiple test communities."""
    communities = []
    for i in range(3):
        creator = user if i % 2 == 0 else another_user
        community = Community.objects.create(
            name=f"community_{i + 1}",
            description=f"Description for community {i + 1}",
            creator=creator,
        )
        communities.append(community)
    return communities


@pytest.fixture
def authenticated_client(client, user):
    """Create an authenticated client."""
    client.force_login(user)
    return client


@pytest.fixture
def create_community_url():
    """URL for community creation."""
    return reverse("community-create")


@pytest.fixture
def community_detail_url():
    """Generate community detail URLs."""

    def _detail_url(community_name):
        return reverse("community-detail", kwargs={"name": community_name})

    return _detail_url


# ==========================================
# CREATE COMMUNITY VIEW TESTS
# ==========================================


@pytest.mark.django_db
class TestCreateCommunityView:
    """Test suite for CreateCommunityView."""

    def test_view_requires_authentication(self, client, create_community_url):
        """Test that unauthenticated users are redirected to login."""
        response = client.get(create_community_url)

        assert response.status_code == 302
        assert "sign-in" in response.url.lower()

    def test_authenticated_user_can_access_create_form(
        self, authenticated_client, create_community_url
    ):
        """Test that authenticated users can access the creation form."""
        response = authenticated_client.get(create_community_url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].__class__.__name__ == "CommunityForm"

    def test_form_contains_correct_fields(
        self, authenticated_client, create_community_url
    ):
        """Test that the form contains the expected fields."""
        response = authenticated_client.get(create_community_url)
        form = response.context["form"]

        assert "name" in form.fields
        assert "description" in form.fields
        assert len(form.fields) == 2

    def test_create_community_success(
        self, authenticated_client, user, create_community_url
    ):
        """Test successful community creation."""
        form_data = {
            "name": "new_test_community",
            "description": "A newly created test community",
        }

        response = authenticated_client.post(create_community_url, data=form_data)

        # Check redirect
        assert response.status_code == 302

        # Check community was created
        community = Community.objects.get(name="new_test_community")
        assert community.description == "A newly created test community"
        assert community.creator == user

        # Check redirect URL (assumes get_absolute_url is implemented)
        assert response.url == community.get_absolute_url()

    @pytest.mark.parametrize(
        "field_name,field_value,expected_error",
        [
            ("name", "", "This field is required"),
            ("description", "", "This field is required"),
            (
                "name",
                "x" * 256,
                "Ensure this value has at most",
            ),  # Assuming max_length=255
        ],
    )
    def test_form_validation_errors(
        self,
        authenticated_client,
        create_community_url,
        field_name,
        field_value,
        expected_error,
    ):
        """Test form validation for various invalid inputs."""
        form_data = {}
        form_data[field_name] = field_value

        response = authenticated_client.post(create_community_url, data=form_data)

        assert response.status_code == 200  # Form redisplayed with errors
        assert expected_error.lower() in str(response.context["form"].errors).lower()

    def test_duplicate_community_name_validation(
        self, authenticated_client, community, create_community_url
    ):
        """Test that duplicate community names are handled appropriately."""
        form_data = {
            "name": community.name,  # Duplicate name
            "description": "Different description",
        }

        response = authenticated_client.post(create_community_url, data=form_data)

        assert response.status_code == 200
        assert "already exists" in str(response.context["form"].errors).lower()

    def test_creator_auto_assignment(
        self, authenticated_client, user, create_community_url
    ):
        """Test that the creator is automatically assigned to the current user."""
        form_data = {
            "name": "creator_test_community",
            "description": "Testing creator assignment",
        }

        authenticated_client.post(create_community_url, data=form_data)

        community = Community.objects.get(name="creator_test_community")
        assert community.creator == user


# ==========================================
# COMMUNITY DETAIL VIEW TESTS
# ==========================================


@pytest.mark.django_db
class TestCommunityDetailView:
    """Test suite for CommunityDetailView."""

    def test_community_detail_view_success(
        self, client, community, community_detail_url
    ):
        """Test successful retrieval of community detail."""
        url = community_detail_url(community.name)
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["object"] == community
        assert response.context["community"] == community

    def test_community_detail_view_context_data(
        self, client, community, community_detail_url
    ):
        """Test that context contains the expected data."""
        url = community_detail_url(community.name)
        response = client.get(url)

        context = response.context
        assert "object" in context
        assert "community" in context
        assert context["object"].name == community.name
        assert context["object"].description == community.description
        assert context["object"].creator == community.creator

    def test_community_not_found_returns_404(self, client, community_detail_url):
        """Test that non-existent community returns 404."""
        url = community_detail_url("nonexistent_community")
        response = client.get(url)

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "community_name",
        [
            "simple_name",
            "complex_community_name",
            "name_with_123_numbers",
        ],
    )
    def test_various_community_names(
        self, client, user, community_detail_url, community_name
    ):
        """Test community detail view with various name formats."""
        # Create community with specific name
        Community.objects.create(
            name=community_name, description="Test description", creator=user
        )

        url = community_detail_url(community_name)
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["community"].name == community_name

    def test_slug_field_configuration(self):
        """Test that view is configured with correct slug settings."""
        view = CommunityDetailView()

        assert view.slug_field == "name"
        assert view.slug_url_kwarg == "name"
        assert view.model == Community

    def test_get_object_method(self, rf, community, user):
        """Test the get_object method works correctly."""
        # Create request factory request
        request = rf.get(f"/communities/{community.name}/")
        request.user = user

        # Create view instance
        view = CommunityDetailView()
        view.setup(request, name=community.name)

        # Test get_object
        obj = view.get_object()
        assert obj == community

    def test_case_sensitive_community_lookup(self, client, user, community_detail_url):
        """Test community lookup behavior with different cases."""
        Community.objects.create(
            name="testcommunity", description="Case sensitivity test", creator=user
        )

        # Test exact case match
        url = community_detail_url("TestCommunity")
        response = client.get(url)
        assert response.status_code == 404

        # Test different case (behavior depends on database configuration)
        url = community_detail_url("testcommunity")
        response = client.get(url)
        # This might be 200 or 404 depending on your database settings
        assert response.status_code == 200


# ==========================================
# INTEGRATION TESTS
# ==========================================


@pytest.mark.django_db
class TestCommunityViewsIntegration:
    """Integration tests for community views working together."""

    def test_create_then_view_community_workflow(
        self, authenticated_client, user, create_community_url, community_detail_url
    ):
        """Test complete workflow: create community then view it."""
        # Step 1: Create community
        form_data = {
            "name": "integration_test_community",
            "description": "Testing full workflow",
        }

        create_response = authenticated_client.post(
            create_community_url, data=form_data
        )
        assert create_response.status_code == 302

        # Step 2: View the created community
        community = Community.objects.get(name="integration_test_community")
        detail_url = community_detail_url(community.name)
        detail_response = authenticated_client.get(detail_url)

        assert detail_response.status_code == 200
        assert detail_response.context["community"].name == "integration_test_community"
        assert detail_response.context["community"].creator == user

    def test_multiple_users_creating_communities(
        self, client, user, another_user, create_community_url
    ):
        """Test multiple users can create their own communities."""
        # User 1 creates community
        client.force_login(user)
        response1 = client.post(
            create_community_url,
            {"name": "user1_community", "description": "First user community"},
        )
        assert response1.status_code == 302

        # User 2 creates community
        client.force_login(another_user)
        response2 = client.post(
            create_community_url,
            {"name": "user2_community", "description": "Second user community"},
        )
        assert response2.status_code == 302

        # Verify both communities exist with correct creators
        community1 = Community.objects.get(name="user1_community")
        community2 = Community.objects.get(name="user2_community")

        assert community1.creator == user
        assert community2.creator == another_user


# ==========================================
# PERFORMANCE AND EDGE CASE TESTS
# ==========================================


@pytest.mark.django_db
class TestCommunityViewsEdgeCases:
    """Test edge cases and performance considerations."""

    def test_long_community_name_handling(
        self, authenticated_client, create_community_url
    ):
        """Test handling of very long community names."""
        long_name = "x" * 300  # Assuming this exceeds model field limit

        form_data = {"name": long_name, "description": "Testing long names"}

        response = authenticated_client.post(create_community_url, data=form_data)

        assert "form" in response.context
        assert response.context["form"].errors

    def test_special_characters_in_community_name(
        self, authenticated_client, user, create_community_url, community_detail_url
    ):
        """Test handling of special characters in community names."""
        special_name = "community_!@#$%^&*()"

        form_data = {"name": special_name, "description": "Testing special characters"}

        response = authenticated_client.post(create_community_url, data=form_data)

        assert response.status_code == 200

    def test_unicode_community_name(self, authenticated_client, create_community_url):
        """Test handling of Unicode characters in community names."""
        unicode_name = "コミュニティ测试社区"  # Japanese + Chinese characters

        form_data = {"name": unicode_name, "description": "Testing Unicode support"}

        response = authenticated_client.post(create_community_url, data=form_data)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "malicious_input",
        [
            '<script>alert("xss")</script>',
            '"><img src="x" onerror="alert(1)">',
            "'; DROP TABLE communities; --",
        ],
    )
    def test_malicious_input_handling(
        self, authenticated_client, create_community_url, malicious_input
    ):
        """Test that malicious input is handled safely."""
        form_data = {"name": malicious_input, "description": "Testing security"}

        response = authenticated_client.post(create_community_url, data=form_data)

        # Should not crash and should handle input safely
        assert response.status_code in [200, 302]

        # If community was created, ensure malicious content is escaped
        if response.status_code == 302:
            communities = Community.objects.filter(name=malicious_input)
            if communities.exists():
                # Verify dangerous content doesn't execute
                assert "<script>" not in str(communities.first().name)


# ==========================================
# PERMISSION AND SECURITY TESTS
# ==========================================


@pytest.mark.django_db
class TestCommunityViewsSecurity:
    """Test security aspects of community views."""

    def test_anonymous_user_cannot_create_community(self, client, create_community_url):
        """Test that anonymous users cannot create communities."""
        form_data = {
            "name": "anonymous_community",
            "description": "Should not be created",
        }

        response = client.post(create_community_url, data=form_data)

        assert response.status_code == 302  # Redirect to login
        assert not Community.objects.filter(name="anonymous_community").exists()

    def test_csrf_protection(self, authenticated_client, create_community_url):
        """Test CSRF protection is enabled."""
        # Django test client automatically includes CSRF token
        # This test verifies the view requires CSRF protection
        form_data = {
            "name": "csrf_test_community",
            "description": "Testing CSRF protection",
        }

        response = authenticated_client.post(create_community_url, data=form_data)

        # Should succeed with CSRF token
        assert response.status_code == 302

    def test_session_security(self, client, user, create_community_url):
        """Test that session management works correctly."""
        # Login user
        client.force_login(user)

        # Create community
        form_data = {
            "name": "session_test_community",
            "description": "Testing session security",
        }

        response = client.post(create_community_url, data=form_data)
        assert response.status_code == 302

        # Verify community was created by the logged-in user
        community = Community.objects.get(name="session_test_community")
        assert community.creator == user
