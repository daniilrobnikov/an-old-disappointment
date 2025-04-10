from abc import ABC, abstractmethod

from numpy.typing import NDArray


class VideoStream(ABC):
    """
    Base class for video stream readers.
    """

    def __str__(self):
        return f"Video stream {self.__hash__()}"

    @abstractmethod
    def get_latest_frame(self) -> NDArray | None:
        pass
