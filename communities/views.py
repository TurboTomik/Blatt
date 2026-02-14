from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView
from django.views.generic.base import View

from posts.mixins import PaginatedViewMixin
from posts.models import Post

from .models import Community, Subscription


class CreateCommunityView(LoginRequiredMixin, CreateView):
    """Handle creation of new community instances with authentication."""

    model = Community
    fields = ["name", "description"]

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Process valid form submission and set the community creator."""
        form.instance.creator = self.request.user
        return super().form_valid(form)


class CommunityDetailView(PaginatedViewMixin, DetailView):
    """Display detailed information for a specific community."""

    model = Community
    slug_field = "name"
    slug_url_kwarg = "name"
    context_object_name = "community"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Extend the default context data with subscription information.

        Returns:
            dict[str, Any]: Context data passed to the template.
        """
        context = super().get_context_data(**kwargs)

        user = self.request.user
        community = self.object

        context["is_subscribed"] = user.is_authenticated and community.is_subscribed_by(
            user
        )

        context["is_community"] = True

        return context

    def get_paginated_queryset(self) -> QuerySet["Post"]:
        """Return posts for the current community ordered by newest first."""
        return (
            Post.objects.filter(community=self.object)
            .select_related("community", "user")
            .order_by("-created_at")
        )


class CommunityJoinView(LoginRequiredMixin, View):
    """Handle a POST request that allows an authenticated user to join a community."""

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        """
        Add the current authenticated user to the specified community.

        URL kwargs:
            name (str): The unique name of the community to join.

        Args:
            request (HttpRequest): The incoming HTTP request.
            *args: Positional arguments passed to the view.
            **kwargs: Keyword arguments containing URL parameters.

        Returns:
            HttpResponse: A redirect response to the community detail page.
        """
        community_name = kwargs["name"]

        community = get_object_or_404(
            Community,
            name=community_name,
        )

        Subscription.objects.subscribe_user(
            user=request.user,
            community=community,
        )

        return redirect("community-detail", name=community_name)


class CommunityLeaveView(LoginRequiredMixin, View):
    """Handle a POST request that allows an authenticated user to leave a community."""

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        """
        Delete the current authenticated user to the specified community.

        URL kwargs:
            name (str): The unique name of the community to leave.

        Args:
            request (HttpRequest): The incoming HTTP request.
            *args: Positional arguments passed to the view.
            **kwargs: Keyword arguments containing URL parameters.

        Returns:
            HttpResponse: A redirect response to the community detail page.
        """
        community_name = kwargs["name"]

        community = get_object_or_404(Community, name=community_name)

        Subscription.objects.unsubscribe_user(
            user=request.user,
            community=community,
        )

        return redirect("community-detail", name=community_name)
