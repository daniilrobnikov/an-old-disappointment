# Script responsible for monitoring the robot workspace through a video stream

from dataclasses import dataclass
from datetime import datetime

from numpy.typing import NDArray


@dataclass
class Detection:
    bounds: tuple[int, int, int, int]
    """Bounding box of the detection in the format of (x, y, w, h)"""
    _class: str
    """Class of the detected object."""


@dataclass
class WorkspaceState:
    """
    Describes objects detected in a snapshot of the robot workspace.
    """

    timestamp: datetime
    frame: NDArray
    detections: list[Detection]


class WorkspaceMonitor:
    """
    Analyzes frames from the workspace camera stream to detect anomalies.
    """

    def __init__(self):
        # TODO: initialize and load model
        pass

    def process(self, frame: NDArray) -> WorkspaceState:
        """Process a frame and return the workspace state."""
