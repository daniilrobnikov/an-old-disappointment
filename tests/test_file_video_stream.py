from pathlib import Path

from icecream import ic

from an_old_disappointment.object_detector.utils import (
    mask_to_bounding_box,
    normalize_bounding_box,
)
from an_old_disappointment.video_stream.file_video_stream import FileVideoStream
from an_old_disappointment.workers.workspace_monitor import WorkspaceMonitor


def test_file_video_stream(workcell_test_video: Path) -> None:
    stream = FileVideoStream(workcell_test_video)
    monitor = WorkspaceMonitor(tracked_objects=["person"])

    while True:
        frame = stream.get_latest_frame()
        if frame is None:
            # video stream is over
            break

        workspace = monitor.process(frame)
        if len(workspace.intrusions) <= 0:
            continue

        intrusions = workspace.intrusions
        ic(intrusions[0])

        # extract bounding box from detection
        box = mask_to_bounding_box(intrusions[0].mask)
        (h, w) = frame.shape[:2]
        box_normalized = normalize_bounding_box(box, (w, h))

        break
