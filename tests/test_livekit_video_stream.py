import os

from dotenv import load_dotenv
import pytest


def test_livekit_video_stream() -> None:
    """
    Test the livekit video stream.
    """

    load_dotenv()

    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

    assert (
        LIVEKIT_URL is not None
        and LIVEKIT_API_KEY is not None
        and LIVEKIT_API_SECRET is not None
    ), (
        "LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be set in the environment variables."
    )

    from an_old_disappointment.video_stream.livekit_video_stream import (
        LiveKitVideoStream,
    )

    streamer = LiveKitVideoStream(
        url=LIVEKIT_URL,
        identity="test_livekit_video_stream",
        room_name="50robotics-cameras",
        track_name="thistrackdoesnotexist",  # <- intentional, to trigger the timeout
        timeout=1,
    )

    with pytest.raises(TimeoutError):
        streamer.start()

    # while True:
    #     frame = streamer.get_latest_frame()
    #     if frame is None:
    #         break
    #
    #     # display the frame
    #     cv2.imshow("LiveKit Video Stream", frame)
    #     cv2.waitKey(1)
