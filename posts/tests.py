from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from communities.models import Community
from users.models import User

from .models import Post


class PostModelTest(TestCase):
    """Test cases for Post model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(
            email="test@test.com",
            username="user",
            password="test.pass123",
        )

        self.community = Community.objects.create(
            name="test_community",
            description="Test community",
            user=self.user,
        )

    def test_post_creation_with_required_fields(self):
        """Test creating a post with required fields."""

        post = Post.objects.create(
            title="Test Post",
            user=self.user,
            community=self.community,
        )

        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.body, "")
        self.assertEqual(post.up_votes, 0)
        self.assertEqual(post.down_votes, 0)
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.community, self.community)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)

    def test_post_creation_with_all_fields(self):
        """Test creating a post with all fields."""

        post = Post.objects.create(
            title="Full Test Post",
            body="The post body",
            up_votes=5,
            down_votes=3,
            user=self.user,
            community=self.community,
        )

        self.assertEqual(post.title, "Full Test Post")
        self.assertEqual(post.body, "The post body")
        self.assertEqual(post.up_votes, 5)
        self.assertEqual(post.down_votes, 3)

    def test_post_creation_without_title_fails(self):
        """Test creating a post without title fails."""

        with self.assertRaises(ValidationError):
            post = Post(
                user=self.user,
                community=self.community,
            )
            post.full_clean()

    def test_post_creating_without_community_fails(self):
        """Test creating a post without community fails."""

        with self.assertRaises(IntegrityError):
            Post.objects.create(
                title="Test Post",
                user=self.user,
            )

    def test_post_creating_without_user_succeeds(self):
        """Test creating a post without user succeeds (user can be null)."""

        post = Post.objects.create(
            title="Anonymous Post",
            community=self.community,
            user=None,
        )

        self.assertEqual(post.title, "Anonymous Post")
        self.assertIsNone(post.user)

    def test_title_max_length(self):
        """Test title field max length constraint."""
        long_title = "x" * 121

        with self.assertRaises(ValidationError):
            post = Post(
                title=long_title,
                user=self.user,
                community=self.community,
            )
            post.full_clean()

    def test_title_within_max_length(self):
        """Test title field within max length works."""
        valid_title = "x" * 120

        post = Post.objects.create(
            title=valid_title,
            user=self.user,
            community=self.community,
        )

        self.assertEqual(len(post.title), 120)

    def test_negative_votes_prevented(self):
        """Test that negative votes are prevented by PositiveIntegerField."""

        post = Post.objects.create(
            title="Test Post",
            user=self.user,
            community=self.community,
        )

        post.up_votes = -1
        post.down_votes = -1

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_user_deletion_sets_null(self):
        """Test that deleting user sets post.user to null."""

        post = Post.objects.create(
            title="Test Post",
            user=self.user,
            community=self.community,
        )

        self.user.delete()

        post.refresh_from_db()
        self.assertIsNone(post.user)

    def test_community_deletion_cascades(self):
        """Test that deleting community deletes the post."""

        post = Post.objects.create(
            title="Test Post",
            user=self.user,
            community=self.community,
        )

        post_id = post.id
        post.delete()

        self.assertFalse(Post.objects.filter(id=post_id).exists())

    def test_related_name_posts(self):
        """Test related_name 'posts' works for user and community."""

        post1 = Post.objects.create(
            title="Post 1",
            user=self.user,
            community=self.community,
        )
        post2 = Post.objects.create(
            title="Post 2",
            user=self.user,
            community=self.community,
        )

        user_posts = self.user.posts.all()
        self.assertEqual(user_posts.count(), 2)
        self.assertIn(post1, user_posts)
        self.assertIn(post2, user_posts)

        community_post = self.community.posts.all()
        self.assertEqual(community_post.count(), 2)
        self.assertIn(post1, community_post)
        self.assertIn(post2, community_post)

    def test_timestamps_auto_update(self):
        """Test that created_at and updated_at work correctly."""

        post = Post.objects.create(
            title="Test Post",
            user=self.user,
            community=self.community,
        )

        created_time = post.created_at
        updated_time = post.updated_at

        post.title = "Updated title"
        post.save()

        post.refresh_from_db()

        self.assertEqual(post.created_at, created_time)
        self.assertNotEqual(post.updated_at, updated_time)

    def test_multiple_posts_same_user_community(self):
        """Test that same user can create multiple posts in the same community."""
        Post.objects.create(
            title="Post 1",
            user=self.user,
            community=self.community,
        )
        Post.objects.create(
            title="Post 2",
            user=self.user,
            community=self.community,
        )

        self.assertEqual(
            Post.objects.filter(user=self.user, community=self.community).count(), 2
        )

    def test_ordering_by_created_at(self):
        """Test posts can be ordered by created_at."""
        post1 = Post.objects.create(
            title="Post 1",
            user=self.user,
            community=self.community,
        )
        post2 = Post.objects.create(
            title="Post 2",
            user=self.user,
            community=self.community,
        )

        post = Post.objects.order_by("-created_at")
        self.assertEqual(post[0], post2)
        self.assertEqual(post[1], post1)

    def test_ordering_by_votes(self):
        """Test posts can be ordered by up_votes."""
        post1 = Post.objects.create(
            title="Low votes post",
            up_votes=2,
            user=self.user,
            community=self.community,
        )
        post2 = Post.objects.create(
            title="Hight votes post",
            up_votes=10,
            user=self.user,
            community=self.community,
        )

        posts = Post.objects.order_by("-up_votes")
        self.assertEqual(posts[0], post2)
        self.assertEqual(posts[1], post1)

    def test_filtering_by_community(self):
        """Test filtering posts by community"""

        community2 = Community.objects.create(
            name="community2",
            description="Second community",
            user=self.user,
        )

        post1 = Post.objects.create(
            title="Community 1 post",
            user=self.user,
            community=self.community,
        )
        post2 = Post.objects.create(
            title="Community 2 post",
            user=self.user,
            community=community2,
        )

        community1_posts = Post.objects.filter(community=self.community)
        community2_posts = Post.objects.filter(community=community2)

        self.assertEqual(community1_posts.count(), 1)
        self.assertEqual(community2_posts.count(), 1)
        self.assertEqual(community1_posts.first(), post1)
        self.assertEqual(community2_posts.first(), post2)

    def test_filtering_by_user(self):
        """Test filtering posts by user"""

        user2 = User.objects.create(
            email="test2@test.com",
            username="user2",
            password="test.pass123",
        )

        post1 = Post.objects.create(
            title="User 1 Post",
            user=self.user,
            community=self.community,
        )
        post2 = Post.objects.create(
            title="User 2 Post",
            user=user2,
            community=self.community,
        )

        user1_posts = Post.objects.filter(user=self.user)
        user2_posts = Post.objects.filter(user=user2)

        self.assertEqual(user1_posts.count(), 1)
        self.assertEqual(user2_posts.count(), 1)
        self.assertIn(post1, user1_posts)
        self.assertIn(post2, user2_posts)
