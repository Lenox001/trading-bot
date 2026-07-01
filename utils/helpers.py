import math
import time

def round_down(value, step):
    """Round down to nearest step (e.g., lot step 0.01)."""
    return math.floor(value / step) * step

def timestamp_now():
    return int(time.time())