from paho.mqtt.client import Client as MqttClient

from .workspace_monitor import WorkspaceState


class WorkspaceStatePublisher:
    def __init__(
        self,
        broker_address: str,
        broker_port: int = 1883,
        topic: str = "workspace/state",
    ):
        """
        Publishes the state of the workspace to an MQTT broker.

        Args:
            broker_address: Address of the MQTT broker.
            broker_port: Port of the MQTT broker.
            topic: MQTT topic to publish the workspace state to.
        """
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client = MqttClient()

        self.topic = topic

    def connect(self) -> None:
        """
        Connect to the MQTT broker.
        """
        self.client.connect(self.broker_address, self.broker_port)

    def publish_state(self, state: WorkspaceState) -> None:
        """
        Publish the state of the workspace to the MQTT broker.
        """

        # TODO: serialize state

        self.client.publish(
            self.topic,
            payload=state,
            qos=1,
            retain=False,
        )
