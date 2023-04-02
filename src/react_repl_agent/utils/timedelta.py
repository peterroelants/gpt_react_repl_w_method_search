from datetime import timedelta


def format_timedelta(td: timedelta) -> str:
    """Format timedelta into 00h00m00s"""
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{int(hours):02}h:{int(minutes):02d}m:{int(seconds):02d}s"
    else:
        if minutes > 0:
            return f"{int(minutes):02d}m:{int(seconds):02d}s"
    return f"{int(seconds):02d}s"
