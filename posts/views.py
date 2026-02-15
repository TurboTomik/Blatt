from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Prefetch, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView
from django.views.generic.edit import HttpResponseRedirect

from .mixins import PaginatedViewMixin
from .models import Post, PostVote


class PostDetailView(DetailView):
    """Display the details of a single Post instance."""

    model = Post
    context_object_name = "post"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add the current user's vote (if any) to the context.

        This allows the vote arrows to be highlighted correctly.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            context["user_vote"] = PostVote.objects.filter(
                user=user, post=self.object
            ).first()
        else:
            context["user_vote"] = None

        return context


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
            queryset = (
                Post.objects.filter(community__subscriptions__user=self.request.user)
                .select_related("user", "community")
                .order_by("-created_at")
            )

            if self.request.user.is_authenticated:
                queryset = queryset.prefetch_related(
                    Prefetch(
                        "post_votes",
                        queryset=PostVote.objects.filter(user=self.request.user),
                        to_attr="current_user_vote",
                    )
                )

            return queryset

        return Post.objects.order_by("-created_at")[:50]


class PostVoteView(LoginRequiredMixin, View):
    """
    Handle upvote and downvote actions for a Post.

    This view supports the following behaviors:

    - Create a new vote if the user has not voted yet.
    - Remove the vote if the user clicks the same vote again.
    - Switch vote if the user changes from upvote to downvote or vice versa.
    - Safely update cached vote counters using F expressions.
    - Return a rendered HTMX partial with the updated vote component.

    Requires authenticated users.
    """

    def post(
        self, request: HttpRequest, pk: int, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Process a vote submission.

        Args:
            request (HttpRequest): The incoming HTTP request.
            pk (int): Primary key of the Post being voted on.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Rendered vote component partial.
        """
        post: Post = get_object_or_404(Post, pk=pk)

        try:
            value: int = int(request.POST.get("value", 0))
        except (TypeError, ValueError):
            return HttpResponseForbidden("Invalid vote value.")

        if value not in (1, -1):
            return HttpResponseForbidden("Invalid vote value.")

        with transaction.atomic():
            vote, created = PostVote.objects.select_for_update().get_or_create(
                user=request.user,
                post=post,
                defaults={"value": value},
            )

            if created:
                if value == 1:
                    post.up_votes = F("up_votes") + 1
                else:
                    post.down_votes = F("down_votes") + 1

            else:
                if vote.value == value:
                    if value == 1:
                        post.up_votes = F("up_votes") - 1
                    else:
                        post.down_votes = F("down_votes") - 1

                    vote.delete()
                else:
                    if value == 1:
                        post.up_votes = F("up_votes") + 1
                        post.down_votes = F("down_votes") - 1
                    else:
                        post.down_votes = F("down_votes") + 1
                        post.up_votes = F("up_votes") - 1

                    vote.value = value
                    vote.save(update_fields=["value"])

            post.save(update_fields=["up_votes", "down_votes"])

        post.refresh_from_db()

        user_vote = PostVote.objects.filter(user=request.user, post=post).first()

        return render(
            request,
            "partials/vote_component.html",
            {"post": post, "user_vote": user_vote},
        )
