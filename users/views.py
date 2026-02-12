from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import DetailView

from communities.models import Community, Subscription
from posts.models import Post

from .forms import UserLoginForm, UserRegisterForm
from .models import User
from .services import UserAuthService


class UserRegisterView(View):
    """
    Handle HTTP requests for user registration.

    This view is responsible only for HTTP request/response handling,
    delegating all business logic to the UserAuthService.

    Attributes:
        form_class: The form class used for user registration.
        template_name: Template path for rendering the registration page.
        service: Service class handling registration business logic.
    """

    form_class = UserRegisterForm
    template_name = "users/sign-up.html"
    service = UserAuthService()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Display the user registration form.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Rendered registration page with empty form.
        """
        form = self.form_class()
        return render(
            request,
            self.template_name,
            {"form": form, "header_alt": True, "no_dock": True},
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Process user registration form submission.

        Validates form data and delegates user creation to the service layer.
        Handles the HTTP response based on the service operation result.

        Args:
            request: The HTTP request object containing POST data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect on success or re-rendered form with errors.
        """
        form = self.form_class(request.POST)

        if form.is_valid():
            result = self.service.register_user(form.cleaned_data)

            if result.success:
                return redirect(result.redirect_url)

            for field, error in result.errors.items():
                form.add_error(field, error)

        return render(request, self.template_name, {"form": form})


class UserLoginView(View):
    """
    Handle HTTP requests for user login.

    This view manages HTTP request/response logic for authentication,
    delegating authentication business logic to the UserAuthService.

    Attributes:
        form_class: The form class used for user login.
        template_name: Template path for rendering the login page.
        service: Service class handling authentication business logic.
    """

    form_class = UserLoginForm
    template_name = "users/sign-in.html"
    service = UserAuthService()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Display the user login form.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Rendered login page with empty form.
        """
        form = self.form_class()
        return render(
            request,
            self.template_name,
            {"form": form, "header_alt": True, "no_dock": True},
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Process user login form submission.

        Validates form data and delegates authentication to the service layer.
        Manages user session based on authentication result.

        Args:
            request: The HTTP request object containing POST data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect on success or re-rendered form with errors.
        """
        form = self.form_class(request.POST)

        if form.is_valid():
            result = self.service.authenticate_user(
                request=request, credentials=form.cleaned_data
            )

            if result.success:
                return redirect(result.redirect_url)
            form.add_error(None, result.error_message)

        return render(request, self.template_name, {"form": form})


class UserPageView(DetailView):
    """
    Display detailed information for a single user.

    This view retrieves a User instance based on the username provided
    in the URL and renders it to the specified template. It handles
    fetching the user object and passing it to the template context
    for display.

    Attributes:
        model: The model class representing users (User).
        context_object_name: The name under which the user object
            is accessible in the template context.
        slug_field: The model field used to look up the user (username).
        slug_url_kwarg: The URL keyword argument that provides the
            username for lookup.
    """

    model = User
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context["posts"] = Post.objects.filter(user=user)
        if self.request.user.is_authenticated:
            context["subscriptions"] = Community.objects.filter(
                subscriptions__user=self.request.user
            )
        else:
            context["subscriptions"] = []

        return context
