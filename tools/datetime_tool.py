"""
Datetime tool — returns current date, time, and timezone info.
"""

import datetime


def datetime_tool(query: str = "") -> str:
    """Return the current date and time in multiple formats.

    Args:
        query: Ignored (tool is called whenever a time/date intent is detected).

    Returns:
        A formatted string with the current UTC and local time info.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_local = datetime.datetime.now()

    return (
        f"🕐 **Current Date & Time**\n"
        f"   - UTC:   `{now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
        f"   - Local: `{now_local.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"   - Day:   `{now_utc.strftime('%A, %B %d %Y')}`\n"
        f"   - Week:  `Week {now_utc.isocalendar()[1]} of {now_utc.year}`"
    )
