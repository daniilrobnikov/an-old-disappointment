from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class LiveKitConfig(BaseModel):
    identity: str
    """Identity of this client"""
    room_name: str
    """Name of the room to connect to"""
    track_name: str
    """Name of the track in the room to subscribe to"""
    url: str
    """URL of the LiveKit server"""
    api_key: str
    """API key for the LiveKit server"""
    api_secret: str
    """API secret for the LiveKit server"""


class MqttConfig(BaseModel):
    broker: str
    """Address of the MQTT broker"""
    port: int
    """Port of the MQTT broker"""
    topic: str
    """Topic to publish the workspace state to"""
    username: str
    """Username for the MQTT broker"""
    password: str
    """Password for the MQTT broker"""


class MonitorConfig(BaseModel):
    tracked_objects: list[str]
    """List of object classes to track in the workspace"""


class Config(BaseSettings):

    class Config:  # <- pydantic's BaseSettings configuration
        env_file = ".env"
        env_nested_delimiter = "."

    livekit: LiveKitConfig
    mqtt: MqttConfig
    monitor: MonitorConfig
    debug: bool = False
