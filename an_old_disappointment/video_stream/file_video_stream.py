import logging
import time
from pathlib import Path

import cv2
from numpy._typing import NDArray


from an_old_disappointment.video_stream.base import VideoStream

log = logging.getLogger(__name__)


class FileVideoStream(VideoStream):
    """
    Streamer for video files.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path.resolve()
        self._capture = None
        self._fps = 0

        self._last_frame_time = 0

    def __str__(self) -> str:
        return f"File Video Stream ({self.file_path})"

    def get_latest_frame(self) -> NDArray | None:
        if self._capture is None:
            self._start_capture()

        current_time = time.perf_counter()
        frame_duration = 1 / self._fps
        next_frame_time = self._last_frame_time + frame_duration

        # wait before reading the next frame if requested too fast
        if current_time < next_frame_time:
            time.sleep(next_frame_time - current_time)

        # skip frames if too slow
        frame = None
        while current_time >= next_frame_time:
            ret, frame = self._capture.read()
            if not ret:
                break

            current_time += frame_duration

        self._last_frame_time = time.perf_counter()

        return frame

    def _start_capture(self):
        if self._capture is not None:
            return

        file_path = str(self.file_path)
        self._capture = cv2.VideoCapture(file_path)
        if not self._capture.isOpened():
            raise IOError(f"Cannot open video file '{file_path}'")

        self._fps = self._capture.get(cv2.CAP_PROP_FPS)

        log.info(f"Streaming from video file '{file_path}' ({self._fps:.2f} FPS)")
