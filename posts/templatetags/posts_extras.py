import datetime

from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name="datesince", expects_localtime=True)
def datesince(d: datetime.datetime | None) -> str:
    """
    Format a datetime as a human-readable relative or absolute time.

    The output format depends on how much time has passed since `d`:

    - More than 1 year ago: abbreviated month and year (e.g. "Feb 25")
    - More than 7 days ago: day and abbreviated month (e.g. "12 Feb")
    - 1-7 days ago: relative days (e.g. "5 days ago")
    - 1 hour-1 day ago: relative hours (e.g. "8h ago")
    - 1 minute-1 hour ago: relative minutes (e.g. "15m ago")
    - Less than 5 seconds ago: "just now"
    - Otherwise: relative seconds (e.g. "42s ago")

    If `d` is ``None`` or evaluates to ``False``, an empty string is returned.

    Naive datetimes are assumed to be in the current Django timezone
    and are converted to timezone-aware values before comparison.

    Args:
        d (datetime.datetime | None): The datetime to format.

    Returns:
        str: A human-readable representation of the time since `d`.
    """
    if not d:
        return ""

    now = timezone.now()

    delta = now - d

    if delta.total_seconds() < 0:
        return ""

    seconds = int(delta.total_seconds())
    days = delta.days

    # Older than a year -> "Feb 25"
    if days > 365:
        return d.strftime("%b %y")

    # Older than a week -> "12 Feb"
    if days > 7:
        return d.strftime("%d %b")

    # Older than a day -> "5 days ago"
    if days > 0:
        return f"{days} days ago"

    # Older than an hour -> "8h ago"
    if seconds >= 3600:
        hours = seconds // 3600
        return f"{hours}h ago"

    # Older than a minute -> "15m ago"
    if seconds >= 60:
        minutes = seconds // 60
        return f"{minutes}min ago"

    # Just now threshold
    if seconds < 5:
        return "just now"

    return f"{seconds}s ago"
