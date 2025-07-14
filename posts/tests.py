import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from communities.models import Community
from users.models import User

from .models import Post


@pytest.fixture
def user():
    """Fixture to return a user instance."""
    return User.objects.create(
        email="test@test.com",
        username="user",
        password="test.pass123",
    )


@pytest.fixture
def user2():
    """Fixture to return an additional user instance."""
    return User.objects.create(
        email="test2@test.com",
        username="user2",
        password="test.pass123",
    )


@pytest.fixture
def community(user):
    """Fixture to return a community instance."""
    return Community.objects.create(
        name="test_community",
        description="Test community",
        user=user,
    )


@pytest.fixture
def community2(user):
    """Fixture to return an additional community instance."""
    return Community.objects.create(
        name="community2",
        description="Second community",
        user=user,
    )


@pytest.fixture
def post(user, community):
    """Fixture to return a post instance."""
    return Post.objects.create(
        title="Test Post",
        user=user,
        community=community,
    )


@pytest.fixture
def post2(user, community):
    """Fixture to return an additional post instance."""
    return Post.objects.create(
        title="Test Post 2",
        user=user,
        community=community,
    )


class TestPostModel:
    """Test cases for Post model."""

    @pytest.mark.django_db
    def test_post_creation_with_required_fields(self, user, community, post):
        """Test creating a post with required fields."""
        assert post.title == "Test Post"
        assert post.body == ""
        assert post.up_votes == 0
        assert post.down_votes == 0
        assert post.user == user
        assert post.community == community
        assert post.created_at is not None
        assert post.updated_at is not None

    @pytest.mark.django_db
    def test_post_creation_with_all_fields(self, user, community):
        """Test creating a post with all fields."""

        post = Post.objects.create(
            title="Full Test Post",
            body="The post body",
            up_votes=5,
            down_votes=3,
            user=user,
            community=community,
        )

        assert post.title, "Full Test Post"
        assert post.body, "The post body"
        assert post.up_votes, 5
        assert post.down_votes, 3

    @pytest.mark.django_db
    def test_post_creation_without_title_fails(self, user, community):
        """Test creating a post without title fails."""

        with pytest.raises(ValidationError):
            post = Post(
                user=user,
                community=community,
            )
            post.full_clean()

    @pytest.mark.django_db
    def test_post_creating_without_community_fails(self, user):
        """Test creating a post without community fails."""

        with pytest.raises(IntegrityError):
            Post.objects.create(
                title="Test Post",
                user=user,
            )

    @pytest.mark.django_db
    def test_post_creating_without_user_succeeds(self, community):
        """Test creating a post without user succeeds (user can be null)."""

        post = Post.objects.create(
            title="Anonymous Post",
            community=community,
            user=None,
        )

        assert post.title == "Anonymous Post"
        assert post.user is None

    @pytest.mark.django_db
    def test_title_max_length(self, user, community):
        """Test title field max length constraint."""
        long_title = "x" * 121

        with pytest.raises(ValidationError):
            post = Post(
                title=long_title,
                user=user,
                community=community,
            )
            post.full_clean()

    @pytest.mark.django_db
    def test_title_within_max_length(self, post):
        """Test title field within max length works."""
        valid_title = "x" * 120

        post.title = valid_title
        post.full_clean()

        assert len(post.title) == 120

    @pytest.mark.django_db
    def test_negative_votes_prevented(self, user, community, post):
        """Test that negative votes are prevented by PositiveIntegerField."""
        post.up_votes = -1
        post.down_votes = -1

        with pytest.raises(ValidationError):
            post.full_clean()

    @pytest.mark.django_db
    def test_user_deletion_sets_null(self, user, post):
        """Test that deleting user sets post.user to null."""
        user.delete()

        post.refresh_from_db()
        assert post.user is None

    @pytest.mark.django_db
    def test_community_deletion_cascades(self, post):
        """Test that deleting community deletes the post."""
        post_id = post.id
        post.delete()

        assert not Post.objects.filter(id=post_id).exists()

    @pytest.mark.django_db
    def test_related_name_posts(self, user, community, post, post2):
        """Test related_name 'posts' works for user and community."""
        user_posts = user.posts.all()
        assert user_posts.count() == 2
        assert post in user_posts
        assert post2 in user_posts

        community_post = community.posts.all()
        assert community_post.count() == 2
        assert post in community_post
        assert post2 in community_post

    @pytest.mark.django_db
    def test_timestamps_auto_update(self, post):
        """Test that created_at and updated_at work correctly."""
        created_time = post.created_at
        updated_time = post.updated_at

        post.title = "Updated title"
        post.save()

        post.refresh_from_db()

        assert post.created_at == created_time
        assert not post.updated_at == updated_time

    @pytest.mark.django_db
    def test_multiple_posts_same_user_community(self, user, community, post, post2):
        """Test that same user can create multiple posts in the same community."""
        assert Post.objects.filter(user=user, community=community).count() == 2

    @pytest.mark.django_db
    def test_ordering_by_created_at(self, post, post2):
        """Test posts can be ordered by created_at."""
        posts = Post.objects.order_by("-created_at")
        assert posts[0] == post2
        assert posts[1] == post

    @pytest.mark.django_db
    def test_ordering_by_votes(self, user, community):
        """Test posts can be ordered by up_votes."""
        post1 = Post.objects.create(
            title="Low votes post",
            up_votes=2,
            user=user,
            community=community,
        )
        post2 = Post.objects.create(
            title="Hight votes post",
            up_votes=10,
            user=user,
            community=community,
        )

        posts = Post.objects.order_by("-up_votes")
        assert posts[0] == post2
        assert posts[1] == post1

    @pytest.mark.django_db
    def test_filtering_by_community(self, user, community, community2):
        """Test filtering posts by community"""
        post1 = Post.objects.create(
            title="Community 1 post",
            user=user,
            community=community,
        )
        post2 = Post.objects.create(
            title="Community 2 post",
            user=user,
            community=community2,
        )
        community1_posts = Post.objects.filter(community=community)
        community2_posts = Post.objects.filter(community=community2)

        assert community1_posts.count() == 1
        assert community2_posts.count() == 1
        assert community1_posts.first() == post1
        assert community2_posts.first() == post2

    @pytest.mark.django_db
    def test_filtering_by_user(self, user, user2, community):
        """Test filtering posts by user"""
        post1 = Post.objects.create(
            title="User 1 Post",
            user=user,
            community=community,
        )
        post2 = Post.objects.create(
            title="User 2 Post",
            user=user2,
            community=community,
        )

        user1_posts = Post.objects.filter(user=user)
        user2_posts = Post.objects.filter(user=user2)

        assert user1_posts.count() == 1
        assert user2_posts.count() == 1
        assert post1 in user1_posts
        assert post2 in user2_posts
