from abc import ABC, abstractmethod

from numpy.typing import NDArray


class VideoStream(ABC):
    """
    Base class for video stream readers.
    """

    def __str__(self):
        return f"Video stream {self.__hash__()}"

    @abstractmethod
    def start(self) -> None:
        """
        Starts the video stream.
        """
        pass

    @abstractmethod
    def get_latest_frame(self) -> NDArray | None:
        """
        Retrieves the last available frame from the video stream.
        Blocks until a frame is available or until the stream ends.

        Returns:
            The latest frame as a numpy array, or None if the stream has ended.
        """
        pass
