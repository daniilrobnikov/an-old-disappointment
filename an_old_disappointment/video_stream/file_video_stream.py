import logging
from pathlib import Path

import cv2
from icecream import ic
from numpy._typing import NDArray

from rich import print

from an_old_disappointment.video_stream.base import VideoStream

log = logging.getLogger(__name__)

class FileVideoStream(VideoStream):
    """
    Streamer for video files.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path.resolve()
        self._video_capture = None

    def __str__(self) -> str:
        return f"File Video Stream ({self.file_path})"

    def get_latest_frame(self) -> NDArray | None:
        if self._video_capture is None:
            file_path = str(self.file_path)
            self._video_capture = cv2.VideoCapture(file_path)
            log.info(f"Streaming from video file '{file_path}'")

        ret, frame = self._video_capture.read()
        if not ret:
            return None

        return frame
