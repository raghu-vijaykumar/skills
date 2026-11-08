"""Pure geometry helpers shared by the DSRNet adapter and the AI entrypoint.

Kept free of torch so callers can plan a run without importing the GPU stack.
"""

from __future__ import annotations

SIZE_MULTIPLE = 32
MIN_SIZE = 64


def working_size(width: int, height: int, max_width: int) -> tuple[int, int]:
    """Return a multiple-of-32 working size that keeps the source aspect.

    ``max_width`` is rounded down to a multiple of 32 as well so the input is
    always divisible by the encoder's downsampling factor.
    """
    if width <= 0 or height <= 0:
        raise ValueError("frame size must be positive")
    target_width = max(SIZE_MULTIPLE,
                       (min(width, max_width) // SIZE_MULTIPLE) * SIZE_MULTIPLE)
    target_height = int(round(height * target_width / width))
    target_height = max(SIZE_MULTIPLE,
                        (target_height // SIZE_MULTIPLE) * SIZE_MULTIPLE)
    return target_width, target_height
