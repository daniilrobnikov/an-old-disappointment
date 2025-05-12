from pathlib import Path

import pytest


@pytest.fixture
def workcell_test_video() -> Path:
    """
    Video file used for testing the workspace monitor.
    """

    return Path(__file__).parent / "resources/workcell_test_video.mp4"
