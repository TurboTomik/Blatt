from django.db import models

from users.models import User


class Community(models.Model):
    name = models.CharField(max_length=30, blank=False, null=False, unique=True)
    description = models.TextField(blank=True, null=False, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, blank=True, null=True, db_index=True
    )

    class Meta:
        db_table = "community"
        ordering = ["name"]

    def __str__(self):
        return f"Community: {self.name}"


class Subscription(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    community = models.ForeignKey(to=Community, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscription"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "community"], name="unique_subscription"
            )
        ]

    def __str__(self):
        return f"{self.user.username} subscribed to {self.community.name}"
