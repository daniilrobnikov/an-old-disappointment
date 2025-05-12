import numpy as np
from numpy.typing import NDArray


BoundingBox = tuple[float, float, float, float]


def mask_to_bounding_box(mask: NDArray) -> BoundingBox:
    """
    Converts a binary mask to a bounding box.

    Args:
        mask: A binary mask of the object.

    Returns:
        A tuple (x1, y1, w, h) representing the bounding box coordinates.
    """
    y_indices, x_indices = np.where(mask > 0)
    x1, x2 = x_indices.min(), x_indices.max()
    y1, y2 = y_indices.min(), y_indices.max()

    w = x2 - x1
    h = y2 - y1

    return x1, y1, w, h


def normalize_bounding_box(
    box: BoundingBox, resolution: tuple[int, int]
) -> BoundingBox:
    """
    Normalize the bounding box coordinates to the range [0, 1].

    Args:
        box: A tuple (x1, y1, w, h) representing the bounding box coordinates.
        resolution: A tuple (width, height) representing the image resolution.

    Returns:
        A tuple (x1, y1, w, h) representing the normalized bounding box coordinates.
    """
    x1, y1, w, h = box
    width, height = resolution

    return (
        x1 / width,
        y1 / height,
        w / width,
        h / height,
    )
