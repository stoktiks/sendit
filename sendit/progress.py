"""Progress bar utilities for terminal display."""

import sys
import time


def get_bar(pct, width=20):
    """Render a progress bar string."""
    filled = pct * width // 100
    bar = "█" * filled + "░" * (width - filled)
    return bar


def format_speed(bytes_per_sec):
    """Format transfer speed."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    else:
        return f"{bytes_per_sec / 1024 / 1024:.1f} MB/s"


def format_eta(remaining_bytes, bytes_per_sec):
    """Format estimated time remaining."""
    if bytes_per_sec <= 0:
        return "--:--"
    seconds = remaining_bytes / bytes_per_sec
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
    else:
        return f"{seconds // 3600:.0f}h {(seconds % 3600) // 60:.0f}m"


class Progress:
    """Terminal progress bar with speed and ETA."""

    def __init__(self, total_bytes, width=24):
        self.total = total_bytes
        self.width = width
        self.start = time.time()
        self.last = 0
        self.last_time = self.start

    def update(self, current):
        """Update the progress bar display."""
        now = time.time()
        elapsed = now - self.start
        pct = current * 100 // self.total if self.total else 0

        # Calculate speed (average over whole transfer + recent burst)
        if elapsed > 0:
            avg_speed = current / elapsed
        else:
            avg_speed = 0

        bar = get_bar(pct, self.width)
        speed_str = format_speed(avg_speed)

        if current < self.total and avg_speed > 0:
            eta_str = format_eta(self.total - current, avg_speed)
        else:
            eta_str = "done"

        sys.stdout.write(
            f"\r  {bar}  {pct:3d}%  {speed_str:>10}  ETA {eta_str}"
        )
        self.last = current
        self.last_time = now
        sys.stdout.flush()

    def done(self):
        """Finalize the progress bar."""
        elapsed = time.time() - self.start
        if self.total:
            bar = get_bar(100, self.width)
            speed_str = format_speed(self.total / elapsed if elapsed > 0 else 0)
            sys.stdout.write(
                f"\r  {bar}  100%  {speed_str:>10}  {elapsed:.1f}s  \n"
            )
        else:
            sys.stdout.write(f"\r  Downloaded in {elapsed:.1f}s\n")
        sys.stdout.flush()
