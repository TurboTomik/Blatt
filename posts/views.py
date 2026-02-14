from django.db.models import QuerySet
from django.forms import ModelForm
from django.views.generic import CreateView, DetailView, TemplateView
from django.views.generic.edit import HttpResponseRedirect

from .mixins import PaginatedViewMixin
from .models import Post


class PostDetailView(DetailView):
    """Display the details of a single Post instance."""

    model = Post
    context_object_name = "post"


class PostCreateView(CreateView):
    """
    View for creating a new Post instance.

    The form includes fields for the post's title, body, and associated community.
    """

    model = Post
    fields = ["title", "body", "community"]

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add author when create form."""
        form.instance.user = self.request.user
        return super().form_valid(form)


class FeedView(PaginatedViewMixin, TemplateView):
    """Display paginated feed of posts."""

    template_name = "posts/feed.html"

    def get_paginated_queryset(self) -> QuerySet["Post"]:
        """Return posts for subscribed communities if authenticated, else latest 50 posts."""
        if self.request.user.is_authenticated:
            return (
                Post.objects.filter(community__subscriptions__user=self.request.user)
                .select_related("user", "community")
                .order_by("-created_at")
            )
        return Post.objects.order_by("-created_at")[:50]
