# Workspace Monitor

Software to monitor the state of the CNC workspace through a video stream.
Video stream is consumed from [LiveKit](https://livekit.io/) and object detection events are posted to the specified
MQTT broker.

## Usage

### Configuration

The following environment variables must be set in the `.env` file:

```
# LiveKit configuration
LIVEKIT.URL=<livekit-websocket-url>
LIVEKIT.API_KEY=<livekit-api-key>
LIVEKIT.API_SECRET=<livekit-api-secret>
LIVEKIT.IDENTITY=<livekit-identity>
LIVEKIT.ROOM_NAME=<livekit-room-name>
LIVEKIT.TRACK_NAME=<livekit-track-name>

# MQTT configuration
MQTT.BROKER=<mqtt-broker-hostname>
MQTT.PORT=<mqtt-broker-port>
MQTT.TOPIC=<mqtt-topic-for-publishing>
MQTT.USERNAME=<mqtt-username>
MQTT.PASSWORD=<mqtt-password>

# Monitor configuration
MONITOR.TRACKED_OBJECTS=["person"]  # JSON array of object types to track

# Debug configuration
DEBUG=false  # Set to true to display video frames
```

### Running locally

To run the application locally:

1. Install uv: https://github.com/astral-sh/uv
2. Create a virtual environment and install the package:
   ```bash
   uv sync
   ```
3. Run the application:
   ```bash
   uv run workspace-monitor
   ```

### Running in Docker

To run the application in Docker:

1. Build the wheel:
   ```bash
   uv build
   ```

2. Build the Docker image:
   ```bash
   docker build -t "5.0-robotics/workspace-monitor" .
   ```

3. Run the Docker container with the .env file:
   ```bash
   docker run -t --env-file ".env" "5.0-robotics/workspace-monitor"
   ```

## Development

For development:

1. Install uv: https://github.com/astral-sh/uv
2. Create a virtual environment and install the package with development dependencies:
   ```bash
   uv sync
   ```

Notes:

- Video stream is read using [LiveKit Python SDK](https://github.com/livekit/python-sdks)
- Inference is done using [YOLOv7](https://github.com/WongKinYiu/yolov7)
- MQTT communication is done using [Paho MQTT](https://github.com/eclipse-paho/paho.mqtt.python) library
- Most of the code is commented, so you can work your way through from `workspace_monitor/main.py`
