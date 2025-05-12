import asyncio
import logging
import threading
import time
from threading import Thread

import cv2
import numpy as np
from icecream import ic
from livekit import api, rtc
from numpy.typing import NDArray

from workspace_monitor.video_stream.base import VideoStream

log = logging.getLogger(__name__)


class LiveKitVideoStream(VideoStream):
    """
    Streamer for LiveKit.
    """

    _WAITING_FOR_FRAME_FLAG = object()
    """Special value used for the latest frame before the first actual frame is received from LiveKit stream."""

    def __init__(
        self,
        url: str,
        identity: str,
        room_name: str,
        track_name: str,
        timeout: int = 5,
    ):
        self.url = str(url)
        self.identity = identity
        self.room_name = room_name
        self.track_name = track_name
        self.timeout = timeout

        self._video_stream = None
        self._latest_frame: NDArray | None = self._WAITING_FOR_FRAME_FLAG

        # LiveKit SDK is async and needs an asyncio loop of its own to run
        # threfore, we are rtunning it in a separate thread
        self._handler_thread: Thread | None = None
        self._frame_lock = threading.Lock()

    def start(self) -> None:
        self._handler_thread = Thread(
            target=self._stream_handler_thread,
            name="LiveKitVideoStreamHandler",
            daemon=True,
        )
        self._handler_thread.start()

        # wait until we have a frame
        frame = self.get_latest_frame()
        if frame is None:
            raise TimeoutError(
                f"Timed out after {self.timeout} seconds waiting for track '{self.track_name}'"
            )

    def _stream_handler_thread(self):
        """
        Thread responsible for grabbing frames from the video stream.
        """
        asyncio.run(self._stream_handler())

    async def _stream_handler(self):
        """
        Coroutine responsible for grabbing frames from the video stream.
        """
        try:
            token = get_room_join_token(self.room_name, self.identity)

            log.info(
                f"Joining room '{self.room_name}' with identity '{self.identity}'..."
            )

            stream = await get_livekit_video_stream(
                url=self.url,
                token=token,
                track_name=self.track_name,
                timeout=self.timeout,
            )

            log.info(f"Located required stream: {stream}")

            async for event in stream:
                frame = event.frame
                image = frame_to_cv2(frame)

                with self._frame_lock:
                    self._latest_frame = image
        finally:
            self._latest_frame = None

    def get_latest_frame(self) -> NDArray | None:
        while self._latest_frame is self._WAITING_FOR_FRAME_FLAG:
            # wait until we have a frame
            log.debug("Waiting for frame...")
            time.sleep(0.5)

        with self._frame_lock:
            if self._latest_frame is None:
                return None

            return self._latest_frame.copy()


def frame_to_cv2(frame: rtc.VideoFrame) -> NDArray:
    """
    Converts LiveKit's video frame to an OpenCV image.
    """

    w, h = frame.width, frame.height

    if frame.type != rtc.VideoBufferType.RGB24:
        frame = frame.convert(rtc.VideoBufferType.RGB24)

    buffer = np.frombuffer(frame.data, dtype=np.uint8)
    buffer = buffer.reshape((h, w, 3))

    # convert from RGB to BGR
    buffer = cv2.cvtColor(buffer, cv2.COLOR_RGB2BGR)

    return buffer


def get_room_join_token(room: str, identity: str) -> str:
    """
    Generates a JWT token for joining a LiveKit room.

    Args:
        room: The name of the room to join.
        identity: The identity of the participant (this client).

    Returns:
        A JWT token for joining the room.
    """
    grant = api.VideoGrants(room=room, room_join=True)
    token = api.AccessToken().with_grants(grant).with_identity(identity)
    return token.to_jwt()


async def get_livekit_video_stream(
    url: str,
    token: str,
    track_name: str,
    timeout: float = 5,
) -> rtc.VideoStream:
    """
    Connects to a LiveKit room and waits for the given video track to be published and then returns the stream from it.

    Args:
        url: The URL of the LiveKit server.
        token: The access token for the room.
        track_name: The name of the track to subscribe to.
        timeout: The maximum time to wait for the track to be published.
            If no track is published within this time, the function will raise a TimeoutError.

    Returns:
        The video stream from the track.
    """

    stream = None  # <- to store the track

    # set up a room connection
    room = rtc.Room()

    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, *_):
        # this callback finds the video track we need and creates a stream from it
        if track.kind != rtc.TrackKind.KIND_VIDEO:
            log.debug(f"Ignoring non-video track {track}")
            return
        if track.name != track_name:
            log.debug(f"Ignoring track '{track}' because it is not '{track_name}'")
            return

        log.info(f"Subscribed to video track '{track.name}' (sid: {track.sid})")
        nonlocal stream
        stream = rtc.VideoStream(track, format=rtc.VideoBufferType.RGB24)

    await room.connect(url, token=token)
    log.debug(f"Connected to LiveKit room '{room.name}'")

    # wait until we receive the stream
    async def wait_for_stream():
        nonlocal stream
        while stream is None:
            log.debug("Waiting for track...")
            await asyncio.sleep(0.5)

        return stream

    try:
        stream = await asyncio.wait_for(wait_for_stream(), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Timed out after {timeout} seconds waiting for track '{track_name}'"
        )

    return stream
