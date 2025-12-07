def duration(seconds: int | float, fmt: str = "hh:mm:ss") -> str:
    """Convert a duration in seconds to a formatted string.

    Args:
        seconds (int | float): The duration in seconds.
        fmt (str, optional): The format string. Defaults to "hh:mm:ss".
            Supported tokens:
                - hh: hours (zero-padded)
                - mm: minutes (zero-padded)
                - ss: seconds (zero-padded)
    Returns:
        str: The formatted duration string.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    formatted = fmt
    formatted = formatted.replace("hh", f"{hours:02}")
    formatted = formatted.replace("mm", f"{minutes:02}")
    formatted = formatted.replace("ss", f"{secs:02}")

    return formatted
