from typing import Optional

from app.parsers.banking_api import BankingAPIParser
from app.parsers.base import BaseParser


class SystemRouter:
    """
    Router for selecting parser strategies based on log content.
    """

    def __init__(self, parsers: list[BaseParser] | None = None) -> None:
        self._parsers: list[BaseParser] = []
        self._parser_by_system: dict[str, BaseParser] = {}

        for parser in parsers or []:
            self.register(parser)

    def register(self, parser: BaseParser) -> None:
        self._parsers.append(parser)
        self._parser_by_system[parser.system_name] = parser

    def detect_system(self, log: dict) -> str:
        parser = self._find_parser(log)
        if not parser:
            return "unknown"
        return parser.system_name

    def parse_log(self, log: dict) -> Optional[dict]:
        parser = self._find_parser(log)
        if not parser:
            return None
        return parser.parse(log)

    def _find_parser(self, log: dict) -> Optional[BaseParser]:
        for parser in self._parsers:
            if parser.can_parse(log):
                return parser
        return None


router = SystemRouter(parsers=[BankingAPIParser()])


def detect_system(log: dict) -> str:
    """
    Backward-compatible function API.
    """
    return router.detect_system(log)


def parse_log(log: dict) -> Optional[dict]:
    """
    Backward-compatible function API.
    """
    return router.parse_log(log)
