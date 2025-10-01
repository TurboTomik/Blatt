from django.shortcuts import render
from django.views.generic import CreateView, DetailView

from .models import Post


class PostDetailView(DetailView):
    """Display the details of a single Post instance."""

    model = Post
    context_object_name = "post"
