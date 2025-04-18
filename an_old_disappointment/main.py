import logging
from pathlib import Path

import cv2
from icecream import ic

from an_old_disappointment.video_stream.file_video_stream import FileVideoStream
from an_old_disappointment.workers.workspace_monitor import WorkspaceMonitor


def main():
    # TODO: connect to the LiveKit room and fetch video_stream frames

    video_file_path = Path(__file__) / "../../tests/resources/workcell_test_video.mp4"
    streamer = FileVideoStream(video_file_path)
    monitor = WorkspaceMonitor(
        tracked_objects=["person"],
    )

    while True:
        frame = streamer.get_latest_frame()
        if frame is None:
            # video stream is over
            break

        cv2.imshow(str(streamer), frame)
        cv2.waitKey(1)

        # TODO: process the frames (e.g., detect stuff and display using OpenCV)
        workspace_state = monitor.process(frame)

        # TODO: send detection results to the MQTT endpoint

    pass


def cli():
    main()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s | %(message)s",
    )

    cli()
