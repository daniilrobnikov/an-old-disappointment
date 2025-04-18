# Script responsible for monitoring the robot workspace through a video stream
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from numpy.typing import NDArray

from ..object_detector.yolo_v7 import YOLOv7, Detection
from ..utils import Stopwatch

log = logging.getLogger(__name__)

DEFAULT_DETECTOR_RESOURCES_DIRECTORY = (
    Path(__file__).parent / "../object_detector/resources"
)
"""
Default path to the directory containing the files required to run the object detector.
"""

DEFAULT_TRACKED_CLASSES = ["person"]
"""
Default list of classes to track.
"""


@dataclass
class WorkspaceState:
    """
    Describes objects detected in a snapshot of the robot workspace.
    """

    timestamp: datetime
    frame: NDArray
    intrusions: list[Detection]


class WorkspaceMonitor:
    def __init__(
        self,
        tracked_objects: list[str],
        detector_resources_path: Path = DEFAULT_DETECTOR_RESOURCES_DIRECTORY,
    ):
        """
        Analyzes frames from the workspace camera stream to detect intrusions.

        Args:
            tracked_objects: List of object classes to track.
                The object detector will only return detections of these classes.
            detector_resources_path: Path to the directory containing the files required to run the object detector.
                This may include the model weights, configuration files, and other resources.
                Individual file paths are to be parsed by the object detector itself.
        """

        if not tracked_objects:
            raise RuntimeError(
                "tracked_classes must not be empty. Workspace monitor needs to know which objects to detect."
            )
        self.tracked_classes = tracked_objects

        # initialize the object detector
        self.detector = YOLOv7(
            weights_file_path=detector_resources_path / "yolov7-mask.pt",
            hyperparameters_file_path=detector_resources_path / "hyp.scratch.mask.yaml",
        )

    def process(self, frame: NDArray) -> WorkspaceState:
        """Process a frame and return the workspace state."""

        with Stopwatch() as sw:
            # detect objects in the frame
            detections = self.detector.detect(frame)
            log.info(f"Detected {len(detections)} objects in {sw}")

        # only keep the detections of the tracked classes
        detections = [
            detection
            for detection in detections
            if detection.class_name in self.tracked_classes
        ]

        return WorkspaceState(
            timestamp=datetime.now(),
            frame=frame,
            intrusions=detections,
        )
