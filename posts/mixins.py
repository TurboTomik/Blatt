from typing import Any

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render


class PaginatedViewMixin:
    """Mixin for adding pagination with htmx support to any view."""

    paginate_by = 10
    partial_template_name = "posts/post_list.html"

    def get_paginated_queryset(self) -> None:
        """Override this to return the queryset to paginate."""
        raise NotImplementedError

    def render_to_response(
        self, context: dict[str, Any], **response_kwargs: Any
    ) -> HttpResponse:
        """Render paginated results, returning a partial template for HTMX requests."""
        queryset = self.get_paginated_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["is_paginated"] = paginator.num_pages > 1

        if self.request.headers.get("HX-Request"):
            return render(self.request, self.partial_template_name, context)
        return super().render_to_response(context, **response_kwargs)
