from typing import Any, Literal

from django import template
from django.forms import CharField, EmailField
from django.forms.boundfield import BoundField
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("components/link.html")
def link(
    label: str,
    url: str = "",
    variant: Literal[
        "primary",
        "inherit",
    ] = "primary",
    hidden: bool = False,
    extra_classes: str = "",
) -> dict[str, str | bool | None]:
    """Component for creating a styled link button."""
    classes = [
        "transition-colors",
        "duration-200",
    ]

    if hidden:
        classes.append("hidden")
    else:
        classes.append("inline")

    variant_classes = {
        "primary": [
            "text-brand",
            "hover:text-brand-hover",
            "active:text-brand-active",
        ],
        "inherit": [
            "text-inherit",
            "hover:text-inherit/10",
            "active:text-inherit/20",
        ],
    }

    classes.extend(variant_classes[variant])

    if url:
        url = reverse(url)

    if extra_classes:
        classes.append(extra_classes)

    return {
        "label": label,
        "url": url,
        "class": " ".join(classes),
    }


@register.inclusion_tag("components/button_link.html")
def button_link(
    label: str,
    url: str = "",
    variant: Literal["primary", "outline", "trans"] = "primary",
    small: bool = False,
    hidden: bool = False,
    full_width: bool = False,
    icon_url: str | None = None,
    extra_classes: str = "",
) -> dict[str, str | bool | None]:
    """Component for creating a styled link button."""
    classes = [
        "items-center",
        "justify-center",
        "font-semibold",
        "rounded-full",
        "transition-colors",
        "duration-200",
        "whitespace-nowrap",
    ]

    if hidden:
        classes.append("hidden")
    else:
        classes.append("inline-flex")

    variant_classes = {
        "primary": [
            "bg-brand",
            "text-gray-50",
            "hover:bg-brand-hover",
            "active:bg-brand-active",
        ],
        "outline": [
            "border-2",
            "border-brand",
            "text-brand",
            "hover:bg-brand",
            "hover:text-gray-50",
            "active:bg-brand-active",
        ],
        "trans": [
            "text-brand",
            "hover:bg-brand/10",
            "active:bg-brand/20",
        ],
    }

    classes.extend(variant_classes[variant])

    if url:
        url = reverse(url)

    if small:
        classes.extend(["px-2", "py-1", "text-sm"])
        if icon_url:
            classes.append("gap-1")
    else:
        classes.extend(["px-3", "py-2"])
        if icon_url:
            classes.append("gap-2")

    if full_width:
        classes.append("w-full")

    if extra_classes:
        classes.append(extra_classes)

    return {
        "label": label,
        "url": url,
        "class": " ".join(classes),
        "icon_url": icon_url,
    }


@register.inclusion_tag("components/input.html")
def input_field(
    name: str,
    input_type: Literal["text", "email", "password", "search"] = "text",
    label: str = "",
    placeholder: str = "",
    value: str = "",
    required: bool = False,
    disabled: bool = False,
    autocomplete: str = "",
    icon: str | Literal["search", "user", "email", "lock", ""] = "",
    error: str = "",
    help_text: str = "",
    full_width: bool = False,
    extra_classes: str = "",
    min_length: int | None = None,
    max_length: int | None = None,
) -> dict:
    """Universal input component with icon support."""
    container_classes = ["flex", "flex-col", "gap-1", "w-full", "h-fit"]

    if extra_classes:
        container_classes.append(extra_classes)

    wrapper_classes = ["relative"]

    input_classes = [
        "bg-stone-100",
        "inline-flex",
        "items-center",
        "justify-center",
        "px-2",
        "py-2",
        "w-full",
        "font-medium",
        "border",
        "border-border",
        "rounded-full",
        "transition-all",
        "duration-200",
        "focus:outline-none",
        "focus:ring-2",
    ]

    if error:
        input_classes.extend(
            [
                "border-red-500",
                "focus:ring-red-500",
                "focus:border-red-500",
            ]
        )
    else:
        input_classes.extend(
            [
                "border-border",
                "focus:ring-brand",
                "focus:border-brand",
            ]
        )

    if disabled:
        input_classes.extend(["bg-gray-500", "cursor-not-allowed", "text-gray-500"])

    if full_width:
        input_classes.append("w-full")

    icon_classes = [
        "absolute",
        "h-5",
        "left-3",
        "top-1/2",
        "transform",
        "-translate-y-1/2",
        "pointer-events-none",
    ]

    if not icon:
        icon_map = {
            "search": "search",
            "email": "email",
            "password": "lock",
        }
        icon = icon_map.get(input_type, "")

    if icon:
        input_classes.append("pl-9")
        input_classes.append("pr-4")
    else:
        input_classes.append("px-4")

    if not autocomplete:
        autocomplete_map = {
            "email": "email",
            "password": "current-password",
        }
        autocomplete = autocomplete_map.get(input_type, "off")

    return {
        "name": name,
        "input_type": input_type,
        "label": label,
        "placeholder": placeholder,
        "value": value,
        "required": required,
        "disabled": disabled,
        "autocomplete": autocomplete,
        "icon": icon,
        "error": error,
        "help_text": help_text,
        "min_length": min_length,
        "max_length": max_length,
        "container_class": " ".join(container_classes),
        "wrapper_class": " ".join(wrapper_classes),
        "input_class": " ".join(input_classes),
        "icon_class": " ".join(icon_classes),
    }


@register.inclusion_tag("components/button.html")
def button(
    label: str,
    button_type: Literal["button", "submit"] = "button",
    variant: Literal["primary", "outline", "trans"] = "primary",
    small: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    full_width: bool = False,
    icon_url: str | None = None,
    extra_classes: str = "",
) -> dict[str, str | bool | None]:
    """Component for creating a styled link button."""
    classes = [
        "items-center",
        "justify-center",
        "font-semibold",
        "rounded-full",
        "transition-colors",
        "duration-200",
        "whitespace-nowrap",
    ]

    if hidden:
        classes.append("hidden")
    else:
        classes.append("flex")

    variant_classes = {
        "primary": [
            "bg-brand",
            "text-gray-50",
            "hover:bg-brand-hover",
            "active:bg-brand-active",
        ],
        "outline": [
            "border-2",
            "border-brand",
            "text-brand",
            "hover:bg-brand",
            "hover:text-gray-50",
            "active:bg-brand-active",
        ],
        "trans": [
            "text-brand",
            "hover:bg-brand/10",
            "active:bg-brand/20",
        ],
    }

    classes.extend(variant_classes[variant])

    if small:
        classes.extend(["px-2", "py-1", "text-sm"])
        if icon_url:
            classes.append("gap-1")
    else:
        classes.extend(["px-3", "py-2"])
        if icon_url:
            classes.append("gap-2")

    if full_width:
        classes.append("w-full")

    if extra_classes:
        classes.append(extra_classes)

    return {
        "label": label,
        "button_type": button_type,
        "class": " ".join(classes),
        "disabled": disabled,
        "icon_url": icon_url,
    }


@register.inclusion_tag("components/form_field.html")
def form_field(field: BoundField, **kwargs: Any) -> dict:
    """Render a Django form field using the input_field component."""
    input_type = "text"
    icon = kwargs.get("icon", "")

    field_instance = field.field

    if isinstance(field_instance, EmailField):
        input_type = "email"
        icon = icon or "email"
    elif isinstance(field_instance, CharField):
        widget_class_name = field_instance.widget.__class__.__name__
        if widget_class_name == "PasswordInput":
            input_type = "password"
            icon = icon or "lock"
        elif widget_class_name == "Textarea":
            input_type = "text"

    return {
        "name": field.name,
        "input_type": input_type,
        "label": field.label,
        "value": field.value() or "",
        "required": field.field.required,
        "error": field.errors[0] if field.errors else "",
        "help_text": field.help_text,
        "icon": icon,
        "placeholder": kwargs.get("placeholder", ""),
        "min_length": getattr(field.field, "min_length", None),
        "max_length": getattr(field.field, "max_length", None),
    }
