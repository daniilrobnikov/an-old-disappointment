import os
from dataclasses import field, dataclass


def from_env(name: str) -> str:
    """
    Reads the environment variable with the given name and returns its value.
    """
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set")
    return value


@dataclass
class LiveKitConfig:
    identity: str
    """Identity of this client"""
    room_name: str
    """Name of the room to connect to"""
    track_name: str
    """Name of the track in the room to subscribe to"""
    url: str = field(default_factory=lambda: from_env("LIVEKIT_URL"))
    """URL of the LiveKit server. Initialized from LIVEKIT_URL env var if not provided explicitly"""
    api_key: str = field(default_factory=lambda: from_env("LIVEKIT_API_KEY"))
    """API key for the LiveKit server. Initialized from LIVEKIT_API_KEY env var if not provided explicitly"""
    api_secret: str = field(default_factory=lambda: from_env("LIVEKIT_API_SECRET"))
    """API secret for the LiveKit server. Initialized from LIVEKIT_API_SECRET env var if not provided explicitly"""


@dataclass
class MqttConfig:
    broker: str
    """Address of the MQTT broker"""
    port: int
    """Port of the MQTT broker"""
    topic: str
    """Topic to publish the workspace state to"""
    username: str = field(default_factory=lambda: from_env("MQTT_USERNAME"))
    """Username for the MQTT broker. Initialized from MQTT_USERNAME env var if not provided explicitly"""
    password: str = field(default_factory=lambda: from_env("MQTT_PASSWORD"))
    """Password for the MQTT broker. Initialized from MQTT_PASSWORD env var if not provided explicitly"""


@dataclass
class MonitorConfig:
    tracked_objects: list[str] = field(default_factory=list)
    """List of object classes to track in the workspace"""


@dataclass
class Config:
    livekit: LiveKitConfig
    mqtt: MqttConfig
    monitor: MonitorConfig
    debug: bool = False
