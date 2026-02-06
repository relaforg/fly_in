from map_parser import Map, Hub, Connection
from typing import Dict, List, Tuple
from drone import Drone


class Solver:
    def __init__(self, map: Map, paths: Dict[str, str],
                 drones: List[Drone]) -> None:
        self.map = map
        self.paths = paths
        self.drones = drones

    def _get_hub_from_coord(self, coord: Tuple[int, int]) -> Hub | None:
        for h in self.map.hubs:
            if (h.coord == coord):
                return (h)
        return (None)

    def _get_hub_from_name(self, hub_name: str) -> Hub | None:
        for h in self.map.hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    def _get_conn(self, src: str, dst: str) -> Connection | None:
        for c in self.map.conns:
            if (c.src == src and c.dst == dst):
                return (c)
        return (None)

    def _get_hub_cost(self, hub: Hub):
        match hub.zone_type:
            case "normal":
                return (1)
            case "restricted":
                return (2)
            case "priority":
                return (1)
            case "blocked":
                return (-1)

    # MANAGE RESTRICTED PISTE considerer la connection comme un hub
    def run(self) -> None:
        state: Dict[str, List[Drone]] = {h.name: []
                                         for h in self.map.hubs[::-1]}
        state[self.map.start.name] = self.drones
        state["transit"] = []
        out = ""
        in_transit: List[Tuple[Drone, Hub]] = []
        while (len(state[self.map.end.name]) < self.map.nb_drones):
            conn: Dict[Tuple[str, str], List[Drone]] = {
                (c.src, c.dst): [] for hub in self.map.hubs
                for c in hub.neighboors}
            step_str = ""
            next_transit: List[Tuple[Drone, Hub]] = []
            for (curr_hub, drones) in state.items():
                if (curr_hub == self.map.end.name):
                    continue
                src = self._get_hub_from_name(curr_hub)
                for d in list(drones):
                    for t in in_transit:
                        if (d == t[0]):
                            state[t[1].name].append(d)
                            d.coord = t[1].coord
                            in_transit.remove(t)
                            state["transit"].remove(t[0])
                            step_str += f" D{d.id}-{t[1].name}"
                            continue
                    if (src is not None):
                        for (i, p) in enumerate(self.paths[src.name]):
                            dest = self._get_hub_from_name(p[0])
                            if (dest is None):
                                continue
                            con = self._get_conn(src.name, dest.name)
                            if (con is None):
                                continue
                            if (dest.name != self.map.end.name and
                                    (dest.max_drones <= len(state[dest.name])
                                     or con.max_link_capacity
                                     <= len(conn[(src.name, dest.name)]))):
                                continue
                            if (i > 0 and self.paths[src.name][0][1] +
                                    self._get_hub_cost(dest) < p[1]):
                                continue
                            if (dest.zone_type == "restricted"):
                                next_transit.append((d, dest))
                                state["transit"].append(d)
                                step_str += f" D{d.id}-{src.name}->{dest.name}"
                            else:
                                state[dest.name].append(d)
                                d.coord = dest.coord
                                step_str += f" D{d.id}-{dest.name}"
                            state[src.name].remove(d)
                            conn[(src.name, dest.name)].append(d)
                            break
            in_transit = next_transit
            out += step_str.strip() + "\n"
        with open("output.txt", "w") as file:
            file.write(out)
