from typing import Iterator, List, Dict, NoReturn
from pydantic import ValidationError
from map import Hub, Connection, Map
from utils import ParsingErrorContext, ParsingError, Utils
from dataclasses import dataclass, field


@dataclass
class ParsingContext:
    line: str = ""
    line_no: int = 0
    key: str = ""
    args: List[str] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)


class MapParser:
    """MapParser class

    Attributes:
        file_path: str
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.line_no: int = 1

    def iter_lines(self) -> Iterator[str]:
        """"Yield file line one by one"""
        try:
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if (len(line) and line[0] != "#"):
                        line = line.rstrip("\n")
                        yield line
                    self.line_no += 1
        except FileNotFoundError:
            raise ParsingError(f"{self.file_path} does not exists")
        except PermissionError:
            raise ParsingError(f"Cannot read file {self.file_path}")

    def _raise_invalid_sintax(self, ctx: ParsingContext) -> NoReturn:
        raise ParsingError(
            "Invalid syntax",
            ParsingErrorContext(
                file=self.file_path,
                line_no=ctx.line_no,
                line=ctx.line,
                col=len(ctx.line)
            ))

    def _raise_precise(self, ctx: ParsingContext, message: str,
                       col: int) -> NoReturn:
        raise ParsingError(
            message,
            ParsingErrorContext(
                file=self.file_path,
                line_no=ctx.line_no,
                line=ctx.line,
                col=col
            ))

    def _raise_all_line(self, ctx: ParsingContext, message: str) -> NoReturn:
        raise ParsingError(
            message,
            ParsingErrorContext(
                file=self.file_path,
                line_no=ctx.line_no,
                line=ctx.line,
                col=0,
                length=len(ctx.line)
            ))

    def _raise_parameters(self, ctx: ParsingContext, message: str) -> NoReturn:
        raise ParsingError(
            message,
            ParsingErrorContext(
                file=self.file_path,
                line_no=ctx.line_no,
                line=ctx.line,
                col=len(ctx.key) + 2,
                length=len(ctx.args) + sum(len(p) for p in ctx.args) - 1
            ))

    def _raise_metadata(self, ctx: ParsingContext, message: str) -> NoReturn:
        offset = len(ctx.key) + 2 + len(ctx.args) + sum(len(p)
                                                        for p in ctx.args)
        raise ParsingError(
            message,
            ParsingErrorContext(
                file=self.file_path,
                line_no=ctx.line_no,
                line=ctx.line,
                col=offset,
                length=len(ctx.line) - offset
            ))

    def _get_parsing_context(self, line: str) -> ParsingContext:
        ctx = ParsingContext()
        ctx.line = line
        ctx.line_no = self.line_no

        # Block key
        ctx.key, sep, tmp = ctx.line.partition(":")
        if (not len(sep) or not len(tmp)):
            self._raise_invalid_sintax(ctx)
        if (":" in tmp):
            self._raise_precise(ctx, "Invalid Sintax",
                                Utils.find_nth_occurence(":", ctx.line, 2))

        # Block args
        args, _, tmp = tmp.partition("[")
        ctx.args = args.split()

        if (not len(tmp)):
            return (ctx)

        # Block attrs
        if (tmp[-1] != "]"):
            self._raise_invalid_sintax(ctx)
        for attr in tmp[:-1].split():
            key, _, value = attr.partition("=")
            if (not len(value)):
                raise ParsingError(
                    "All metadata must have a value",
                    ParsingErrorContext(
                        file=self.file_path,
                        line_no=ctx.line_no,
                        line=ctx.line,
                        col=len(ctx.key) + 3 + sum(len(p) for p in ctx.args)
                        + len(ctx.args),
                        length=len(key)
                    ))
            if (ctx.attrs.get(key) is not None):
                self._raise_all_line(
                    ctx, f"{key} metadata has already been set")
            ctx.attrs[key] = value
        return (ctx)

    def _validate_hub_ctx(self, ctx: ParsingContext) -> None:
        if (len(ctx.args) != 3):
            self._raise_parameters(ctx, "The number of paramters is wrong")
        if ("-" in ctx.args[0]):
            self._raise_parameters(ctx, "Hub name cannot contain '-'")
        try:
            int(ctx.args[1])
            int(ctx.args[2])
        except ValueError:
            self._raise_parameters(
                ctx, "Hub coordinates must be valid integers")

        for (key, value) in ctx.attrs.items():
            if (key == "max_drones"):
                try:
                    if (int(value) <= 0):
                        self._raise_metadata(ctx, "max_drone value must be "
                                             "a valid positive integer")
                except ValueError:
                    self._raise_metadata(
                        ctx, "max_drone value must be a valid integer")
            elif (key == "zone"):
                if (value not in
                        ["normal", "restricted", "blocked", "priority"]):
                    self._raise_metadata(ctx, "Unknown zone type")
            elif (key == "color"):
                continue
            else:
                self._raise_metadata(ctx, f"Unknown {key} attribute")

    def _validate_nb_drone_ctx(self, ctx: ParsingContext) -> None:
        if (len(ctx.args) != 1):
            self._raise_parameters(ctx, "The number of paramters is wrong")
        try:
            if (int(ctx.args[0]) <= 0):
                self._raise_parameters(
                    ctx, "nb_drones must be a valid positive integer")
        except ValueError:
            self._raise_parameters(ctx, "nb_drones must be a valid integer")
        if (len(ctx.attrs)):
            self._raise_metadata(ctx, "nb_drones does not take any attribute")

    def _validate_connection_ctx(self, ctx: ParsingContext) -> None:
        if (len(ctx.args) != 1):
            self._raise_parameters(ctx, "The number of paramters is wrong")
        if (len(ctx.args[0].split("-")) != 2):
            self._raise_parameters(ctx, "You can only connect two hubs")
        for (key, value) in ctx.attrs.items():
            if (key == "max_link_capacity"):
                try:
                    if (int(value) <= 0):
                        self._raise_metadata(ctx, "max_link_capacity must be "
                                             "a valid positive integer")
                except ValueError:
                    self._raise_metadata(
                        ctx, "max_link_capacity must be a valid integer")
            else:
                self._raise_metadata(ctx, f"Unknown {key} attribute")

    def _validate_ctx(self, ctx: ParsingContext) -> None:
        if (ctx.key in ["start_hub", "end_hub", "hub"]):
            self._validate_hub_ctx(ctx)
        elif (ctx.key == "nb_drones"):
            self._validate_nb_drone_ctx(ctx)
        elif (ctx.key == "connection"):
            self._validate_connection_ctx(ctx)
        else:
            raise ParsingError(
                f"{ctx.key} unknown key",
                ParsingErrorContext(
                    file=self.file_path,
                    line_no=ctx.line_no,
                    line=ctx.line,
                    col=0,
                    length=len(ctx.key)
                ))

    def _get_nb_drones(self, ctx: ParsingContext) -> int:
        if (ctx.key != "nb_drones"):
            self._raise_all_line(
                ctx, "The first line must be the number of drones")
        return (int(ctx.args[0]))

    def _add_hub(self, ctx: ParsingContext, hubs: List[Hub]) -> Hub:
        try:
            hub = Hub(
                name=ctx.args[0],
                coord=(int(ctx.args[1]), int(ctx.args[2])),
                zone_type=ctx.attrs.get("zone", "normal"),
                color=ctx.attrs.get("color", "white"),
                max_drones=int(ctx.attrs.get("max_drones", 1)),
            )
        except ValidationError:
            self._raise_all_line(ctx, "A problem occured during hub creation")
        if (Utils.get_hub_by_name(hub.name, hubs) is not None):
            self._raise_all_line(ctx,  f"{hub.name} already exists")
        hubs.append(hub)
        return (hub)

    def _add_connection(self, ctx: ParsingContext,
                        connections: List[Connection],
                        hubs: List[Hub]) -> None:
        names = ctx.args[0].split("-")
        hub1 = Utils.get_hub_by_name(names[0], hubs)
        hub2 = Utils.get_hub_by_name(names[1], hubs)
        if (hub1 is None or hub2 is None):
            self._raise_parameters(
                ctx, "You can only connect previously declared hub")
        if (hub1 == hub2):
            self._raise_all_line(ctx, "Connection cannot connect the same hub")
        if (Utils.get_connection((hub1, hub2), connections) is not None):
            self._raise_all_line(ctx, "Connection already exists")
        try:
            con = Connection(
                hubs=(hub1, hub2),
                max_link_capacity=int(ctx.attrs.get("max_link_capacity", 1))
            )
        except ValidationError:
            self._raise_all_line(
                ctx, "A problem occured during Connection creation")
        connections.append(con)

    def run(self) -> Map:
        nb_drones: int | None = None
        hubs: List[Hub] = []
        connections: List[Connection] = []
        start: Hub | None = None
        end: Hub | None = None
        for line in self.iter_lines():
            ctx = self._get_parsing_context(line)
            self._validate_ctx(ctx)
            if (nb_drones is None):
                nb_drones = self._get_nb_drones(ctx)
            if ("hub" in ctx.key):
                tmp = self._add_hub(ctx, hubs)
                if ("start" in ctx.key):
                    if (start is None):
                        start = tmp
                    else:
                        self._raise_all_line(
                            ctx, "Start position has already been set")
                if ("end" in ctx.key):
                    if (end is None):
                        end = tmp
                    else:
                        self._raise_all_line(
                            ctx, "End position has already been set")
            elif (ctx.key == "connection"):
                self._add_connection(ctx, connections, hubs)
        if (start is None or end is None):
            raise ParsingError("You must provide a start and end position")
        if (nb_drones is None):
            raise ParsingError("You must provide a number of drone")
        try:
            return (Map(
                start=start,
                end=end,
                nb_drones=nb_drones,
                hubs=hubs,
                connections=connections
            ))
        except ValidationError:
            raise ParsingError("An error occured during Map creation")
