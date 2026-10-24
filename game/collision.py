"""Collision helpers with an optional pybind11 acceleration module."""

try:
    from _collision_engine import circle_collisions as _native_collisions
except ImportError:
    _native_collisions = None


def collision_pairs(first, second):
    """Return intersecting circle index pairs; circles are (x, y, radius)."""
    if _native_collisions is not None:
        return _native_collisions(first, second)
    pairs = []
    for i, (x1, y1, r1) in enumerate(first):
        for j, (x2, y2, r2) in enumerate(second):
            dx, dy = x1 - x2, y1 - y2
            radius = r1 + r2
            if dx * dx + dy * dy <= radius * radius:
                pairs.append((i, j))
    return pairs


def engine_name():
    return "C++ COLLISION" if _native_collisions is not None else "PYTHON COLLISION"
