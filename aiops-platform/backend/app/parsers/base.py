from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Strategy interface for system-specific log parsers.
    """

    @property
    @abstractmethod
    def system_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def can_parse(self, log: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, log: dict) -> dict:
        raise NotImplementedError
