from django.forms import ModelForm
from django.views.generic import CreateView, DetailView
from django.views.generic.edit import HttpResponseRedirect

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
