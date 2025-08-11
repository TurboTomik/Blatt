from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.utils import timezone

from .models import Community, Subscription

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="Testpass!123",
    )


@pytest.fixture
def another_user():
    """Create another test user."""
    return User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="Testpass!123",
    )


@pytest.fixture
def community(user):
    """Create a test community."""
    return Community.objects.create_community(
        name="test_community",
        creator=user,
    )


@pytest.fixture
def another_community(user):
    """Create another test community."""
    return Community.objects.create_community(
        name="another_community",
        creator=user,
    )


class TestCommunityModel:
    """Test cases for the Community model."""

    @pytest.mark.django_db
    def test_community_creation_with_all_fields(self, user):
        """Test creating a community with all fields."""
        community = Community.objects.create(
            name="full_community",
            description="A community with all fields",
            creator=user,
        )

        assert community.name == "full_community"
        assert community.description == "A community with all fields"
        assert community.creator == user
        assert community.created_at is not None
        assert isinstance(community.created_at, datetime)

    @pytest.mark.django_db
    def test_community_creation_minimal_fields(self):
        """Test creating a community with only required fields."""
        community = Community.objects.create(name="minimal_community")

        assert community.name == "minimal_community"
        assert community.description == ""  # Default value
        assert community.creator is None  # Can be null
        assert community.created_at is not None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "valid_name",
        [
            "gaming",
            "3gamin",
            "gam1ng",
            "gamin3",
            "gaming_3",
            "gaming_pc",
            "steam_games",
            "steam_games_achievements",
        ],
    )
    def test_valid_community_name(self, valid_name):
        """Test that valid community names are accepted."""
        Community.objects.create(name=valid_name)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "invalid_name",
        [
            "_gaming",
            "gaming_",
            "_steam_games",
            "steam_games_",
            "_steam_games_",
            "steam__games_pc",
            "steam____games",
            "Gaming",
            "_Gaming",
            "SteamGames",
        ],
    )
    def test_invalid_community_name(self, invalid_name):
        """Test that invalid community names are not accepted."""
        with pytest.raises(ValidationError):
            Community.objects.create(name=invalid_name)

    @pytest.mark.django_db
    def test_community_name_uniqueness(self, user):
        """Test that community names must be unique."""
        Community.objects.create(name="unique_name", creator=user)

        with pytest.raises(ValidationError):
            Community.objects.create(name="unique_name", creator=user)

    @pytest.mark.django_db
    def test_community_name_min_length(self, user):
        """Test community name min length constraint."""
        short_name = "aa"

        community = Community(name=short_name, creator=user)
        with pytest.raises(ValidationError):
            community.full_clean()

    @pytest.mark.django_db
    def test_community_name_max_length(self, user):
        """Test community name max length constraint."""
        long_name = "a" * 31  # Exceeds max_length=30

        community = Community(name=long_name, creator=user)
        with pytest.raises(ValidationError):
            community.full_clean()

    @pytest.mark.django_db
    def test_community_name_not_str(self, user):
        """Test that a ValidationError is raised when the community name is not a string."""
        community = Community(name=11, creator=user)
        with pytest.raises(ValidationError):
            community.full_clean()

    @pytest.mark.django_db
    def test_community_name_cannot_be_blank(self):
        """Test that community name cannot be blank."""
        community = Community(name="", description="Test")

        with pytest.raises(ValidationError):
            community.full_clean()

    @pytest.mark.django_db
    def test_community_name_cannot_be_none(self):
        """Test that community name cannot be None."""
        with pytest.raises(ValidationError):
            Community.objects.create(name=None)

    @pytest.mark.django_db
    def test_community_description_can_be_blank(self, user):
        """Test that description can be blank."""
        community = Community.objects.create(
            name="testuser",
            description="",
            creator=user,
        )
        assert community.description == ""

    @pytest.mark.django_db
    def test_community_description_default_value(self, user):
        """Test that description has correct default value."""
        community = Community.objects.create(name="testuser", creator=user)
        assert community.description == ""

    @pytest.mark.django_db
    def test_community_description_strip(self, user):
        """Test that leading and trailing whitespaces are removed from the community description."""
        community = Community.objects.create(
            name="testuser",
            description="    Test Description   ",
            creator=user,
        )
        assert community.description == "Test Description"

    @pytest.mark.django_db
    def test_community_user_can_be_null(self):
        """Test that user field can be null."""
        community = Community.objects.create(name="no_user_community")
        assert community.creator is None

    @pytest.mark.django_db
    def test_community_user_set_null_on_delete(self, user):
        """Test that user is set to null when user is deleted."""
        community = Community.objects.create(name="test_community", creator=user)

        user.delete()
        community.refresh_from_db()

        assert community.creator is None

    @pytest.mark.django_db
    def test_community_ordering(self, user):
        """Test that communities are ordered by name."""
        Community.objects.create(name="zebra_community", creator=user)
        Community.objects.create(name="alpha_community", creator=user)
        Community.objects.create(name="beta_community", creator=user)

        communities = list(Community.objects.all())
        names = [c.name for c in communities]

        assert names == ["alpha_community", "beta_community", "zebra_community"]

    @pytest.mark.django_db
    def test_community_str_representation(self, user):
        """Test the string representation of Community."""
        community = Community.objects.create(name="test_community", creator=user)
        expected_str = f"Community: {community.name}"
        assert str(community) == expected_str

    @pytest.mark.django_db
    def test_community_repr_representation(self, user):
        """Test the repr representation of Community."""
        community = Community.objects.create(name="test_community", creator=user)
        expected_str = f"<Community(id={community.id}, name='{community.name}')>"
        assert repr(community) == expected_str

    @pytest.mark.django_db
    def test_community_created_at_auto_now_add(self, user):
        """Test that created_at is automatically set on creation."""
        before_creation = timezone.now()
        community = Community.objects.create(name="time_test", creator=user)
        after_creation = timezone.now()

        assert before_creation <= community.created_at <= after_creation

    @pytest.mark.django_db
    def test_community_created_at_not_updated(self, user):
        """Test that created_at is not updated on save."""
        community = Community.objects.create(name="time_test", creator=user)
        original_time = community.created_at

        community.description = "Updated description"
        community.save()

        assert community.created_at == original_time

    @pytest.mark.django_db
    def test_get_community_by_name(self, community):
        """Test that a community can be found by its name."""
        assert community == Community.objects.get_by_name(community.name)

    @pytest.mark.django_db
    def test_get_community_by_name_fail(self, community):
        """Test that the 'get_by_name' method returns None when no community is found."""
        assert not Community.objects.get_by_name("politic")

    @pytest.mark.django_db
    def test_get_community_by_name_not_str(self, community):
        """Test that a TypeError is raised when the input is not a string."""
        with pytest.raises(TypeError):
            assert not Community.objects.get_by_name(11)

    @pytest.mark.django_db
    def test_search_community_by_name(self, community):
        """Test that a communities can be found by its name."""
        assert community in Community.objects.search_by_name(community.name)

    @pytest.mark.django_db
    def test_search_community_by_name_fail(self, community):
        """Test that a communities cannot be found by wrong name."""
        query_set = Community.objects.search_by_name("politic")
        assert isinstance(query_set, QuerySet)
        assert not query_set

    @pytest.mark.django_db
    def test_search_community_by_name_not_str(self, community):
        """Test that a TypeError is raised when the input is not a string."""
        with pytest.raises(TypeError):
            assert not Community.objects.search_by_name(11)

    @pytest.mark.django_db
    def test_subscribers_count(self, user, another_user, community):
        """Test that correct count of subscribers in a community."""
        assert community.subscriber_count == 1

        Subscription.objects.create(user=another_user, community=community)

        assert community.subscriber_count == 2

    @pytest.mark.django_db
    def test_subscribed_by(self, user, another_user, community):
        """Test that the 'is_subscribed_by' function correctly checks user subscription status."""
        assert community.is_subscribed_by(user=user)
        assert not community.is_subscribed_by(user=another_user)


class TestSubscriptionModel:
    """Test cases for the Subscription model."""

    @pytest.mark.django_db
    def test_subscription_creation(self, another_user, community):
        """Test creating a subscription."""
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )

        assert subscription.user == another_user
        assert subscription.community == community
        assert subscription.subscribed_at is not None
        assert isinstance(subscription.subscribed_at, datetime)

    @pytest.mark.django_db
    def test_subscription_creating_without_user(self, user, community):
        """Test creating a subscription without user."""
        with pytest.raises(ValidationError, match="(?i)user is required"):
            Subscription.objects.create(user=None, community=community)

    @pytest.mark.django_db
    def test_subscription_creating_without_community(self, user):
        """Test creating a subscription without community."""
        with pytest.raises(ValidationError, match="(?i)community is required"):
            Subscription.objects.create(user=user)

    @pytest.mark.django_db
    def test_subscription_unique_constraint(self, user, community):
        """Test that user can't subscribe to the same community twice."""
        with pytest.raises(ValidationError):
            Subscription.objects.create(user=user, community=community)

    @pytest.mark.django_db
    def test_subscription_different_users_same_community(
        self,
        user,
        another_user,
        community,
    ):
        """Test that different users can subscribe to the same community."""
        sub1 = Subscription.objects.get(user=user)
        sub2 = Subscription.objects.create(user=another_user, community=community)

        assert sub1.user != sub2.user
        assert sub1.community == sub2.community

    @pytest.mark.django_db
    def test_subscription_same_user_different_communities(
        self,
        another_user,
        community,
        another_community,
    ):
        """Test that same user can subscribe to different communities."""
        sub1 = Subscription.objects.create(user=another_user, community=community)
        sub2 = Subscription.objects.create(
            user=another_user,
            community=another_community,
        )

        assert sub1.user == sub2.user
        assert sub1.community != sub2.community

    @pytest.mark.django_db
    def test_subscription_user_cascade_delete(self, another_user, community):
        """Test that subscription is deleted when user is deleted."""
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )
        subscription_id = subscription.id

        another_user.delete()

        assert not Subscription.objects.filter(id=subscription_id).exists()

    @pytest.mark.django_db
    def test_subscription_community_cascade_delete(self, another_user, community):
        """Test that subscription is deleted when community is deleted."""
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )
        subscription_id = subscription.id

        community.delete()

        assert not Subscription.objects.filter(id=subscription_id).exists()

    @pytest.mark.django_db
    def test_subscription_str_representation(self, user, community):
        """Test the string representation of Subscription."""
        subscription = Subscription.objects.get(user=user, community=community)
        expected_str = f"{user.username} subscribed to {community.name}"

        assert str(subscription) == expected_str

    @pytest.mark.django_db
    def test_subscription_repr_representation(self, user, community):
        """Test the repr representation of Subscription."""
        subscription = Subscription.objects.get(user=user, community=community)
        expected_str = (
            f"<Subscription(user='{user.username}', community='{community.name}')>"
        )

        assert repr(subscription) == expected_str

    @pytest.mark.django_db
    def test_subscription_subscribed_at_auto_now_add(self, another_user, community):
        """Test that subscribed_at is automatically set on creation."""
        before_creation = timezone.now()
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )
        after_creation = timezone.now()

        assert before_creation <= subscription.subscribed_at <= after_creation

    @pytest.mark.django_db
    def test_subscription_subscribed_at_not_updated(self, another_user, community):
        """Test that subscribed_at is not updated on save."""
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )
        original_time = subscription.subscribed_at

        # Save again
        subscription.save()

        assert subscription.subscribed_at == original_time

    @pytest.mark.django_db
    def test_subscribe_user(self, another_user, community):
        """Test that 'subscribe_user' correctly subscribes a user to a community and prevents duplicate subscriptions."""
        assert Subscription.objects.subscribe_user(
            user=another_user,
            community=community,
        )

        assert not Subscription.objects.subscribe_user(
            user=another_user,
            community=community,
        )

    @pytest.mark.django_db
    def test_unsubscribe_user(self, another_user, community):
        """Test that 'unsubscribe_user' correctly unsubscribes a user to a community."""
        Subscription.objects.subscribe_user(
            user=another_user,
            community=community,
        )

        assert Subscription.objects.unsubscribe_user(another_user, community)
        assert not Subscription.objects.unsubscribe_user(another_user, community)


class TestModelRelationships:
    """Test relationships between models."""

    @pytest.mark.django_db
    def test_user_communities_relationship(self, user):
        """Test accessing communities created by a user."""
        community1 = Community.objects.create(name="community_one", creator=user)
        community2 = Community.objects.create(name="community_two", creator=user)
        Community.objects.create(name="community_three")  # No user

        user_communities = Community.objects.filter(creator=user)

        assert community1 in user_communities
        assert community2 in user_communities
        assert len(user_communities) == 2

    @pytest.mark.django_db
    def test_user_subscriptions_relationship(
        self,
        another_user,
        community,
        another_community,
    ):
        """Test accessing subscriptions for a user."""
        sub1 = Subscription.objects.create(user=another_user, community=community)
        sub2 = Subscription.objects.create(
            user=another_user,
            community=another_community,
        )

        user_subscriptions = Subscription.objects.filter(user=another_user)

        assert sub1 in user_subscriptions
        assert sub2 in user_subscriptions
        assert len(user_subscriptions) == 2

    @pytest.mark.django_db
    def test_community_subscriptions_relationship(self, user, another_user, community):
        """Test accessing subscriptions for a community."""
        sub1 = Subscription.objects.get(user=user, community=community)
        sub2 = Subscription.objects.create(user=another_user, community=community)

        community_subscriptions = Subscription.objects.filter(community=community)

        assert sub1 in community_subscriptions
        assert sub2 in community_subscriptions
        assert len(community_subscriptions) == 2


class TestEdgeCases:
    """Test edge cases and potential bugs."""

    @pytest.mark.django_db
    def test_community_name_whitespace_handling(self):
        """Test how community handles whitespace in names."""
        community = Community.objects.create(name="  test_community  ")
        assert community.name == "test_community"

    @pytest.mark.django_db
    def test_subscription_with_deleted_user_reference(self, another_user, community):
        """Test subscription behavior when user is referenced but then deleted."""
        subscription = Subscription.objects.create(
            user=another_user,
            community=community,
        )

        another_user.delete()

        assert not Subscription.objects.filter(id=subscription.id).exists()

    @pytest.mark.django_db
    def test_multiple_subscriptions_performance(self, community):
        """Test creating many subscriptions (basic performance test)."""
        users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="Testpass!123",
            )
            users.append(user)

        # Create subscriptions
        subscriptions = []
        for user in users:
            subscription = Subscription.objects.create(user=user, community=community)
            subscriptions.append(subscription)

        # Verify all were created
        assert Subscription.objects.filter(community=community).count() == 101

    @pytest.mark.django_db
    def test_community_description_very_long(self, user):
        """Test community with very long description."""
        long_description = "a" * 1000  # Very long description
        with pytest.raises(ValidationError):
            Community.objects.create(
                name="long_desc_community",
                description=long_description,
                creator=user,
            )
