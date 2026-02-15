from django.db import models
from django.urls import reverse

from communities.models import Community
from users.models import User


class Post(models.Model):
    """Represent a post in a community."""

    title = models.CharField(max_length=120, blank=False, null=False, db_index=True)
    body = models.TextField(blank=True, null=False, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    up_votes = models.PositiveIntegerField(default=0, db_index=True)
    down_votes = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        related_query_name="post",
        db_index=True,
    )
    community = models.ForeignKey(
        to=Community,
        on_delete=models.CASCADE,
        related_name="posts",
        related_query_name="post",
        db_index=True,
    )

    class Meta:
        db_table = "post"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["community", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-up_votes", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Post: {self.title}"

    def get_absolute_url(self) -> str:
        """Return the absolute URL of this community instance."""
        return reverse("post-detail", kwargs={"pk": self.pk})

    @property
    def votes(self) -> int:
        """Return the net vote score (upvotes minus downvotes)."""
        return self.up_votes - self.down_votes


class PostVote(models.Model):
    """
    Represent a single user's vote on a Post.

    Each user may vote only once per post.
    A vote can either be an upvote (+1) or a downvote (-1).

    This model enables:
    - Preventing duplicate votes
    - Allowing vote toggling
    - Allowing vote switching
    - Tracking which users voted
    """

    UP = 1
    DOWN = -1

    VOTE_CHOICES = (
        (UP, "Upvote"),
        (DOWN, "Downvote"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="post_votes",
        related_query_name="post_vote",
        help_text="The user who cast the vote.",
    )

    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        related_name="post_votes",
        related_query_name="post_vote",
        help_text="The post being voted on.",
    )

    value = models.SmallIntegerField(
        choices=VOTE_CHOICES,
        help_text="The vote value: +1 for upvote, -1 for downvote.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the vote was created.",
    )

    class Meta:
        """Enforce one vote per user per post."""

        db_table = "post_vote"
        unique_together = ("user", "post")
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "Post Vote"
        verbose_name_plural = "Post Votes"

    def __str__(self) -> str:
        """Return a readable string representation of the vote."""
        return f"PostVote(user={self.user_id}, post={self.post_id}, value={self.value})"
