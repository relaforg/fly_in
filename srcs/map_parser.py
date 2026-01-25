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
    def __init__(self, message: str, ctx: Optional[ParseContext] = None):
        super().__init__(self._format(message, ctx))
        self.message = message
        self.ctx = ctx

    @staticmethod
    def _format(message: str, ctx: Optional[ParseContext]) -> str:
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
    to: str = Field(min_length=1)
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


class MapParser:
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
        self.metadata: Dict = {}

    def iter_lines(self) -> Iterator[str]:
        """"Yield file line one by one"""
        with open(self.file_path, "r") as file:
            for line in file:
                line = line.strip()
                if (len(line) and line[0] != "#"):
                    self.line = line.rstrip("\n")
                    yield self.line
                self.no_line += 1

    def format_validation_error(self, e: ValidationError) -> str:
        """Format ValidationError for them to be more clear

        e -- The ValidationError to format
        """
        lines = []
        for err in e.errors():
            field = ".".join(str(p) for p in err["loc"])
            msg = err["msg"]
            lines.append(f"- {field}: {msg}")
        return ("Invalid configuration:\n" + "\n".join(lines))

    @staticmethod
    def find_nth_occurence(c: str, s: str, n: int) -> int:
        index = -1
        for i in range(n):
            index = s.find(c, index + 1)
        return (index)

    def _parse_attrs(self, s: str) -> dict:
        try:
            s = s.strip("[]")
            parts = s.split()
            return dict(p.split("=", 1) for p in parts)
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

    def _split_line(self):
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

    def _raise_parameter_error(self, message: str):
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

    def _get_nbr_drones(self):
        if (self.field != "nb_drones"):
            raise ParsingError(
                "The first line must be the number of drone")
        if (len(self.parameters) != 1):
            self._raise_parameter_error("nb_drones only takes one value")
        try:
            return (int(self.parameters[0]))
        except ValueError:
            raise ParsingError(
                "Number of drones must be an integer",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + 2,
                    length=len(self.parameters[0])
                ))

    def _raise_start_end_duplicate(self, hub: str):
        raise ParsingError(
            f"You must provide only one {hub} position",
            ParseContext(
                file=self.file_path,
                line_no=self.no_line,
                line=self.line,
                col=0,
                length=len(self.field)
            ))

    def _add_hub(self, hub_list: List[Hub]):
        try:
            return (hub_list.append(Hub(
                name=self.parameters[0],
                coord=self._coords_to_2tuple(self.parameters[1:3]),
                zone_type=self.metadata.get("zone", "normal"),
                color=self.metadata.get("color", "white"),
                max_drones=self.metadata.get("max_drones", 1)
            )))
        except ValidationError:
            raise ParsingError(
                "Hub parameters are not valid",
                ParseContext(
                    file=self.file_path,
                    line_no=self.no_line,
                    line=self.line,
                    col=len(self.field) + 2,
                    length=len(self.line) - (len(self.field) + 2)
                ))

    def _find_hub(self, hub_name: str, hub_list: List[Hub]):
        try:
            return ([h for h in hub_list if h.name == hub_name][0])
        except IndexError:
            raise ParsingError(
                f"You can connect {hub_name} hub, it does not exist",
                ParseContext(
                    file=self.file_path,
                ))

    def _handle_connection(self, hub_list: List[Hub]) -> None:
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
        for i in range(2):
            con = Connection(
                to=hubs[i],
                max_link_capacity=self.metadata.get(
                    "max_link_capacity", 1)
            )
            hub = self._find_hub(hubs[(i + 1) % 2], hub_list)
            hub.neighboors.append(con)

    def extract(self) -> Map:
        nb_drones: int = 0
        start: Hub | None = None
        end: Hub | None = None
        hub_list: List[Hub] = []
        for _ in self.iter_lines():
            self._split_line()
            if (not nb_drones):
                nb_drones = self._get_nbr_drones()
                continue
            if (self.field == "start_hub"):
                if (len(self.parameters) != 3):
                    self._raise_parameter_error("Hub parameters are incorrect")
                if (start is not None):
                    self._raise_start_end_duplicate("start")
                self._add_hub(hub_list)
                start = hub_list[-1]
            if (self.field == "end_hub"):
                if (len(self.parameters) != 3):
                    self._raise_parameter_error("Hub parameters are incorrect")
                if (end is not None):
                    self._raise_start_end_duplicate("end")
                self._add_hub(hub_list)
                end = hub_list[-1]
            if (self.field == "hub"):
                if (len(self.parameters) != 3):
                    self._raise_parameter_error("Hub parameters are incorrect")
                self._add_hub(hub_list)
            if (self.field == "connection"):
                self._handle_connection(hub_list)
        if start is None or end is None:
            raise ParsingError(
                "You must provide both a start and end hub",
                ParseContext(
                    file=self.file_path,
                ))
        return (Map(
            start=start,
            end=end,
            nb_drones=nb_drones,
            hubs=hub_list
        ))
