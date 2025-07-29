from django.db import models

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
        indexes = [
            models.Index(fields=["community", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-up_votes", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Post: {self.title}"
