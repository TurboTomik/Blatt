from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView

from .models import Community


class CreateCommunityView(LoginRequiredMixin, CreateView):
    """Handle creation of new community instances with authentication."""

    model = Community
    fields = ["name", "description"]

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Process valid form submission and set the community creator."""
        form.instance.creator = self.request.user
        return super().form_valid(form)


class CommunityDetailView(DetailView):
    """Display detailed information for a specific community."""

    model = Community
    slug_field = "name"
    slug_url_kwarg = "name"
