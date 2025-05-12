import base64
import datetime
import io
import json
import logging
import time

from PIL import Image
from numpy.typing import NDArray
from paho.mqtt.client import Client as MqttClient
from pydantic import BaseModel

from an_old_disappointment.object_detector.utils import (
    BoundingBox,
    mask_to_bounding_box,
    normalize_bounding_box,
)

from .workspace_monitor import WorkspaceState

log = logging.getLogger(__name__)


class BoxDetection(BaseModel):
    """
    Describes an object detected in a snapshot of the robot workspace.
    """

    class_name: str
    """Class name of the detected object"""
    confidence: float
    """Confidence of the detection"""
    box: BoundingBox
    """Bounding box of the detected object in the image frame, in format (x, y, w, h), aka top left corner and dimensions"""


class WorkspaceStateMessage(BaseModel):
    """
    Message to be published to the MQTT broker.
    """

    timestamp: datetime.datetime
    """Timestamp of the frame"""
    frame: dict
    """Base64 encoded image frame"""
    resolution: tuple[int, int]
    """Resolution of the image frame"""
    intrusions: list[BoxDetection]
    """List of detected objects in the frame"""


def encode_frame_base64_jpeg(frame: NDArray) -> dict:
    """
    Encodes the image frame as a base64 string (JPEG).
    """
    with io.BytesIO() as output:
        img = Image.fromarray(frame)
        img.save(output, format="JPEG")
        data = output.getvalue()

    base64_str = base64.b64encode(data).decode("utf-8")

    return {
        "mime": "image/jpeg",
        "data": base64_str,
    }


class WorkspaceStatePublisher:
    def __init__(
        self,
        broker_address: str,
        broker_port: int = 1883,
        topic: str = "workspace/state",
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Publishes the state of the workspace to an MQTT broker.

        Args:
            broker_address: Address of the MQTT broker.
            broker_port: Port of the MQTT broker.
            topic: MQTT topic to publish the workspace state to.
            username: Username for the MQTT broker.
            password: Password for the MQTT broker.
        """
        self.broker_address = broker_address
        self.broker_port = broker_port

        self.client = MqttClient()
        if username and password:
            self.client.username_pw_set(username, password)
            self.client.tls_set()

        self.topic = topic

    def connect(self, timeout: float = 5) -> None:
        """
        Connect to the MQTT broker.
        Blocks until the connection is established.

        Args:
            timeout: Timeout for the connection attempt.
        """
        log.info(
            f"Connecting to MQTT broker at '{self.broker_address}:{self.broker_port}'..."
        )

        # initiate the connection
        self.client.connect(self.broker_address, self.broker_port)
        self.client.loop_start()

        # wait for the connection to be established
        start_time = time.perf_counter()
        while not self.client.is_connected():
            if time.perf_counter() - start_time > timeout:
                self.client.loop_stop()
                raise TimeoutError(f"MQTT connection to '{self.broker_address}:{self.broker_port}' timed out after {timeout} seconds")

            log.debug("Waiting for MQTT client to connect...")

        log.info("MQTT client connected")

    def publish_state(self, state: WorkspaceState) -> None:
        """
        Publish the state of the workspace to the MQTT broker.
        """

        (h, w) = state.frame.shape[:2]

        # convert intrusion detections to bounding boxes
        intrusions = []
        for i in state.intrusions:
            # mask to normalized bounding box
            box = mask_to_bounding_box(i.mask)
            box = normalize_bounding_box(box, (w, h))

            # convert to a serializable model
            intrusion = BoxDetection(
                class_name=i.class_name,
                confidence=i.confidence,
                box=box,
            )
            intrusions.append(intrusion)

        # craft a serializable workspace state
        state_message = WorkspaceStateMessage(
            timestamp=state.timestamp,
            frame=encode_frame_base64_jpeg(state.frame),
            resolution=(w, h),
            intrusions=intrusions,
        )

        # publish
        data = state_message.model_dump(mode="json")
        self.client.publish(
            self.topic,
            payload=json.dumps(data),
            qos=1,
            retain=False,
        )

        log.debug(
            f"Published workspace state to MQTT broker '{self.broker_address}:{self.broker_port}' with topic '{self.topic}'"
        )
