from typing import Literal

from django import template
from django.urls import reverse

register = template.Library()


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
        "bg-gray-50",
        "inline-flex",
        "items-center",
        "justify-center",
        "px-2",
        "py-2",
        "w-full",
        "font-semibold",
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
                "border-gray-300",
                "focus:ring-brand",
                "focus:border-brand",
            ]
        )

    if disabled:
        input_classes.extend(["bg-gray-100", "cursor-not-allowed", "text-gray-500"])
    else:
        input_classes.append("bg-white")

    if full_width:
        input_classes.append("w-full")

    label_classes = ["text-sm", "font-medium", "text-gray-700"]
    if required:
        label_classes.append("after:content-['*']")
        label_classes.append("after:ml-0.5")
        label_classes.append("after:text-red-500")

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
        "label_class": " ".join(label_classes),
        "icon_class": " ".join(icon_classes),
    }
