from map import Hub, Connection, List
from typing import Tuple, Optional
from collections import Counter
from dataclasses import dataclass


class Utils:
    """Utility class"""

    @staticmethod
    def get_hub_travel_cost(hub: Hub) -> int:
        """Get hub travel cost

        Args:
            hub: Hub

        Returns:
            int
        """
        match hub.zone_type:
            case "normal" | "priority":
                return (1)
            case "restricted":
                return (2)
            case _:
                return (-1)

    @staticmethod
    def get_connection(couple: Tuple[Hub, Hub],
                       connections: List[Connection]) -> Connection | None:
        """Find the connection connecting the couple's hubs

        Args:
            couple: Tuple[Hub, Hub]
            connections: List[Connection]

        Returns:
            Connection | None
        """
        for c in connections:
            if (Counter((h.name for h in couple))
                    == Counter((h.name for h in c.hubs))):
                return (c)
        return (None)

    @staticmethod
    def get_hub_by_name(hub_name: str, hubs: List[Hub]) -> Hub | None:
        """Find the hub with the name hub_name

        Args:
            hub_name: str
            hubs: List[Hub]

        Returns:
            Hub | None
        """
        for h in hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    @staticmethod
    def get_connection_by_name(con_name: str, connections: List[Connection]) \
            -> Connection | None:
        """Find the connection with the name con_name

        Args:
            con_name: str
            connections: List[Connection]

        Returns:
            Connection | None
        """
        for c in connections:
            if (c.name == con_name):
                return (c)
        return (None)

    @staticmethod
    def find_nth_occurence(c: str, s: str, n: int) -> int:
        """Find the nth occurence of c in s

        Args:
            c: str
            s: str
            n: int

        Returns:
            int
        """
        index = -1
        for i in range(n):
            index = s.find(c, index + 1)
        return (index)


@dataclass
class ParsingErrorContext:
    """Error context

    Attributes:
        file: str
        line_no: int
        line: str
        col: int
        length: int
        hint: str
    """
    file: Optional[str] = None
    line_no: Optional[int] = None
    line: Optional[str] = None
    col: Optional[int] = None
    length: int = 1
    hint: Optional[str] = None


class ParsingError(Exception):
    """ParsingError custom error

    Attributes:
        message: str
        ctx: ParseContext
    """

    def __init__(self, message: str,
                 ctx: Optional[ParsingErrorContext] = None):
        super().__init__(self._format(message, ctx))
        self.message = message
        self.ctx = ctx

    @staticmethod
    def _format(message: str, ctx: Optional[ParsingErrorContext]) -> str:
        """Format error message

        Args:
            message: str
            ctx: ParseContext

        Returns:
            str
        """
        def c(text: str, code: str) -> str:
            """Aplly color code to str

            Args:
                text: str
                code: str

            Returns:
                str
            """
            return f"\x1b[{code}m{text}\x1b[0m"

        BOLD_RED = "31;1"
        GREY = "90"
        BOLD_YELLOW = "33;1"

        if ctx is None:
            return f"{c('ParsingError: ', BOLD_RED)}{message}"

        message = f"{c('ParsingError: ', BOLD_RED)}{message}"

        if ctx.file is not None or ctx.line_no is not None:
            message += "\n"
            if ctx.file is not None:
                message += c("at " + ctx.file, GREY)
            if ctx.line_no is not None:
                message += c(f":line {ctx.line_no}", GREY)

        if ctx.line is not None:
            message += "\n"
            src = ctx.line.rstrip("\n")
            prefix = ""
            if ctx.line_no is not None:
                prefix = f"{ctx.line_no} | "
            message += prefix + src

            if ctx.col is not None:
                message += "\n" + " " * \
                    (len(prefix) + ctx.col) + "^" * ctx.length

        if ctx.hint:
            message += c(f"\nHint: {ctx.hint}", BOLD_YELLOW)

        return (message)
