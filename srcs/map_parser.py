from pydantic import ValidationError, BaseModel, Field
from pathlib import Path
import os
from typing import Iterator, Tuple, List, Optional, Dict
from dataclasses import dataclass


@dataclass(frozen=True)
class ParseContext:
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

    def __init__(self, message: str, ctx: Optional[ParseContext] = None):
        super().__init__(self._format(message, ctx))
        self.message = message
        self.ctx = ctx

    @staticmethod
    def _format(message: str, ctx: Optional[ParseContext]) -> str:
        """Format error message

        Args:
            message: str
            ctx: ParseContext

        Returns:
            str
        """
        def c(text: str, code: str) -> str:
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


class Connection(BaseModel):
    src: str = Field(min_length=1)
    dst: str = Field(min_length=1)
    max_link_capacity: int = Field(ge=1, default=1)


class Hub(BaseModel):
    name: str = Field(min_length=1)
    coord: Tuple[int, int] = Field(max_length=2, min_length=2)
    zone_type: str = Field(default="normal")
    color: str = Field(default="white")
    max_drones: int = Field(ge=1, default=1)
    neighboors: List[Connection] = Field(default_factory=list)


class Map(BaseModel):
    start: Hub = Field()
    end: Hub = Field()
    nb_drones: int = Field(ge=1)
    hubs: List[Hub] = Field(default_factory=list)
    conns: List[Connection] = Field(default_factory=list)


class MapParser:
    """MapPaerser class

    Attributes:
        no_line: int
        line: str
        field: str
        parameters: List[str]
        metadata: Dict[str, str]
    """

    def __init__(self, file_path: str) -> None:
        if Path(file_path).is_file() and os.access(file_path, os.R_OK):
            self.file_path = file_path
        else:
            raise FileNotFoundError(
                f"{file_path} does not exist or is not readable")
        self.no_line = 1
        self.line: str = ""
        self.field: str = ""
        self.parameters: List[str] = []
        self.metadata: Dict[str, str] = {}

    def iter_lines(self) -> Iterator[str]:
        """"Yield file line one by one"""
        with open(self.file_path, "r") as file:
            for line in file:
                line = line.strip()
                if (len(line) and line[0] != "#"):
                    self.line = line.rstrip("\n")
                    yield self.line
                self.no_line += 1

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

    def _validate_hub_metadata(self, key: str, value: str,
                               offset: int) -> None:
        """Check if hub metadata are correct

        Args:
            key: str
            value: str
            offset: int

        Raises:
            ParsingError
        """
        if (key == "zone" and value not in
                ["normal", "restricted", "priority", "blocked"]):
            raise ParsingError(
                f"Zone {value} not supported",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=offset + len(self.field) +
                    sum(len(x) for x in self.parameters)
                    + len(self.parameters) + 4 + len(key),
                    length=len(str(value))
                ))
        elif (key == "max_drones" and int(value) <= 0):
            raise ValueError

    def _validate_metadata(self, metadata: Dict[str, str]) -> None:
        """Check if metadata are correct

        Args:
            metadata: Dict[str, str]

        Raises:
            ParsingError
        """
        offset = 0
        if ("hub" in self.field):
            try:
                for (key, value) in metadata.items():
                    if (key not in ["color", "zone", "max_drones"]):
                        raise ParsingError(
                            "Invalid metadata parameter",
                            ParseContext(
                                file=self.file_path,
                                line_no=self.no_line,
                                line=self.line,
                                col=offset + len(self.field) +
                                sum(len(x) for x in self.parameters)
                                + len(self.parameters) + 3,
                                length=len(key) + len(str(value)) + 1
                            ))
                    self._validate_hub_metadata(key, value, offset)
                    offset += len(key) + len(str(value)) + 2
            except ValueError:
                raise ParsingError(
                    "Max drone property must be a positive integer",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=offset + len(self.field) +
                        sum(len(x) for x in self.parameters)
                        + len(self.parameters) + 4 + len(key),
                        length=len(str(value))
                    ))

        elif (self.field == "connection"):
            try:
                for (key, value) in metadata.items():
                    if (key != "max_link_capacity"):
                        raise ParsingError(
                            "Invalid metadata parameter",
                            ParseContext(
                                file=self.file_path,
                                line_no=self.no_line,
                                line=self.line,
                                col=offset + len(self.field) +
                                sum(len(x) for x in self.parameters)
                                + len(self.parameters) + 3,
                                length=len(key) + len(str(value)) + 1
                            ))
                    elif (key == "max_link_capacity" and int(value) <= 0):
                        raise ValueError
                    offset += len(key) + len(str(value)) + 2
            except ValueError:
                raise ParsingError(
                    "Max link capacity property must"
                    "be a positive integer",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=offset + len(self.field) +
                        sum(len(x) for x in self.parameters)
                        + len(self.parameters) + 4 + len(key),
                        length=len(str(value))
                    ))

    def _parse_attrs(self, s: str) -> Dict[str, str]:
        """Separate metadata attributes

        Args:
            s: str

        Returns:
            Dict[str, str]

        Raises:
            ParsingError
        """
        try:
            s = s.strip("[]")
            parts = s.split()
            metadata = dict(p.split("=", 1) for p in parts)
            self._validate_metadata(metadata)
            return (metadata)
        except ValueError:
            raise ParsingError(
                "Metadata syntax invalid",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + sum(len(x) for x in self.parameters)
                    + len(self.parameters) + 3,
                    length=len(s)
                ))

    def _split_line(self) -> None:
        """Separate each line sections, field, params, metadata

        Raises:
            ParsingError
        """
        try:
            self.field, value = self.line.split(":")
            self.parameters = value.split("[")[0].strip().split()
            if ("[" in value or "]" in value):
                if ("[" not in value):
                    raise ParsingError(
                        "Metadata syntax invalid",
                        ParseContext(
                            file=self.file_path,
                            line_no=self.no_line,
                            line=self.line,
                            col=len(self.field) + 2,
                            length=sum(len(x) for x in self.parameters) +
                            len(self.parameters) - 1
                        ))
                elif ("]" not in value):
                    raise ParsingError(
                        "Metadata syntax invalid",
                        ParseContext(
                            file=self.file_path,
                            line_no=self.no_line,
                            line=self.line,
                            col=len(self.line) - 1,
                        ))
                metadata = value[self.find_nth_occurence(
                    "[", value, 1):].strip()
                self.metadata = self._parse_attrs(metadata)
            else:
                self.metadata = {}
        except ValueError:
            raise ParsingError(
                "Syntax Error", ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=self.find_nth_occurence(":", self.line, 2),
                ))

    def _coords_to_2tuple(self, coords: List[str]) -> Tuple[int, int]:
        """Convert str coordinates to tuple coordinates

        Args:
            coords: List[str]

        Returns:
            Tuple[int, int]

        Raises:
            ParsingError
        """
        try:
            return (int(coords[0]), int(coords[1]))
        except ValueError:
            raise ParsingError(
                "Coordinate must be integers",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + len(self.parameters[0]) + 3,
                    length=sum(len(x) for x in coords) + len(coords) - 1
                ))

    def _raise_parameter_error(self, message: str) -> None:
        """Raise a error on parameters

        Args:
            message: str

        Raises:
            ParsingError
        """
        raise ParsingError(
            message,
            ParseContext(
                file=self.file_path,
                line_no=self.no_line,
                line=self.line,
                col=len(self.field) + 2,
                length=sum([len(x) for x in self.parameters]
                           ) + len(self.parameters) - 1,
            ))

    def _get_nbr_drones(self) -> int:
        """Get the number of drones

        Returns:
            int

        Raises:
            ParsingError
        """
        if (self.field != "nb_drones"):
            raise ParsingError(
                "The first line must be the number of drone")
        if (len(self.parameters) != 1):
            self._raise_parameter_error("nb_drones only takes one value")
        try:
            nb = int(self.parameters[0])
            if (nb <= 0):
                raise ParsingError(
                    "Number of drones must a potitive integer",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=len(self.field) + 2,
                        length=len(self.parameters[0])
                    ))
            return (nb)
        except ValueError:
            raise ParsingError(
                "Number of drones must be a positive integer",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + 2,
                    length=len(self.parameters[0])
                ))

    def _raise_start_end_duplicate(self, hub: str) -> None:
        """Raise error if start or end is duplicate

        Args:
            hub: str

        Raises:
            ParsingError
        """
        raise ParsingError(
            f"You must provide only one {hub} position",
            ParseContext(
                file=self.file_path,
                line_no=self.no_line,
                line=self.line,
                col=0,
                length=len(self.field)
            ))

    def _add_hub(self, hub_list: List[Hub]) -> None:
        """Add hub to hub list

        Args:
            hub_list: List[Hub]

        Raises:
            ParsingError
        """
        hub = self._find_hub(self.parameters[0], hub_list)
        if (not len(hub)):
            if ("-" in self.parameters[0]):
                raise ParsingError(
                    f"{self.parameters[0]} is not a valid name",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=len(self.field) + 2,
                        length=len(self.parameters[0])
                    ))
            hub_list.append(Hub(
                name=self.parameters[0],
                coord=self._coords_to_2tuple(self.parameters[1:3]),
                zone_type=self.metadata.get("zone", "normal"),
                color=self.metadata.get("color", "white"),
                max_drones=int(self.metadata.get("max_drones", 1))
            ))
            return (None)
        raise ParsingError(
            f"{self.parameters[0]} hub already exist",
            ParseContext(
                file=self.file_path,
                line_no=self.no_line,
                line=self.line,
                col=0,
                length=len(self.field)
            ))

    def _find_hub(self, hub_name: str, hub_list: List[Hub]) -> List[Hub]:
        """Find hub in hub_list by name

        Args:
            hub_name: str
            hub_list: List[Hub]

        Returns:
            List[Hub]
        """
        return ([h for h in hub_list if h.name == hub_name])

    def _handle_connection(self, hub_list: List[Hub],
                           conn_list: List[Connection]) -> None:
        """Handle connection parsing

        Args:
            hub_list: List[Hub]
            conn_list: List[Connection]

        Raises:
            ParsingError
        """
        if (len(self.parameters) != 1):
            self._raise_parameter_error(
                "connection only takes one value")
        hubs = self.parameters[0].split("-")
        if (len(hubs) != 2):
            raise ParsingError(
                "Connections can only connect two hubs",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + 2,
                    length=len(self.parameters[0])
                ))
        for c in conn_list:
            if (hubs[0] == c.src and hubs[1] == c.dst
                    or hubs[1] == c.src and hubs[0] == c.dst):
                raise ParsingError(
                    "Connection already exist",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=len(self.field) + 2,
                        length=len(self.parameters[0])
                    ))
        hub1 = self._find_hub(hubs[0], hub_list)
        hub2 = self._find_hub(hubs[1], hub_list)
        if (not len(hub1)):
            self._hub_dont_exist_error(hubs[0])
        if (not len(hub2)):
            self._hub_dont_exist_error(hubs[1])
        for i in range(2):
            cap = int(self.metadata.get("max_link_capacity", 1))
            hub = self._find_hub(hubs[(i + 1) % 2], hub_list)[0]
            con = Connection(
                src=hub.name,
                dst=hubs[i],
                max_link_capacity=cap
            )
            conn_list.append(con)
            hub.neighboors.append(con)

    def _hub_dont_exist_error(self, hub_name: str) -> None:
        """Raise error when hub dont exists

        Args:
            hub_name: str

        Raises:
            ParsingError
        """
        raise ParsingError(
            f"hub {hub_name} does not exist",
            ParseContext(
                file=self.file_path,
                line_no=self.no_line,
                line=self.line,
                col=len(self.field) + 2,
                length=len(self.parameters[0])
            ))

    def extract(self) -> Map:
        """Parse a map file

        Returns:
            Map

        Raises:
            ParsingError
        """
        nb_drones: int = -1
        start: Hub | None = None
        end: Hub | None = None
        hub_list: List[Hub] = []
        conn_list: List[Connection] = []
        for _ in self.iter_lines():
            self._split_line()
            if (nb_drones < 0):
                nb_drones = self._get_nbr_drones()
            elif ("hub" in self.field and len(self.parameters) != 3):
                self._raise_parameter_error("Hub parameters are incorrect")
            elif (self.field == "start_hub"):
                if (start is not None):
                    self._raise_start_end_duplicate("start")
                self._add_hub(hub_list)
                start = hub_list[-1]
            elif (self.field == "end_hub"):
                if (end is not None):
                    self._raise_start_end_duplicate("end")
                self._add_hub(hub_list)
                end = hub_list[-1]
            elif (self.field == "hub"):
                self._add_hub(hub_list)
            elif (self.field == "connection"):
                self._handle_connection(hub_list, conn_list)
            else:
                raise ParsingError(
                    "Unknown Field",
                    ParseContext(
                        file=self.file_path,
                        line_no=self.no_line,
                        line=self.line,
                        col=0,
                        length=len(self.line)
                    ))
        if start is None or end is None:
            raise ParsingError(
                "You must provide both a start and end hub",
                ParseContext(
                    file=self.file_path,
                ))
        try:
            return (Map(
                start=start,
                end=end,
                nb_drones=nb_drones,
                hubs=hub_list,
                conns=conn_list
            ))
        except ValidationError:
            raise ParsingError(
                "A problem occured during map validation",
                ParseContext(
                    file=self.file_path
                ))
