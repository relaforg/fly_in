from map_parser import Map, Hub
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

    # MANAGE RESTRICTED PISTE considerer la connection comme un hub
    def run(self):
        state = {h.name: [] for h in self.map.hubs[::-1]}
        state[self.map.start.name] = self.drones
        out = ""
        while (len(state[self.map.end.name]) < self.map.nb_drones):
            step_str = ""
            for (curr_hub, drones) in state.items():
                if (curr_hub == self.map.end.name):
                    continue
                src = self._get_hub_from_name(curr_hub)
                for d in list(drones):
                    for p in self.paths[src.name]:
                        dest = self._get_hub_from_name(p[0])
                        if (dest.name != self.map.end.name and
                                dest.max_drones <= len(state[dest.name])):
                            continue
                        state[src.name].remove(d)
                        state[dest.name].append(d)
                        d.coord = dest.coord
                        step_str += f" D{d.id}-{dest.name}"
                        break
            out += step_str.strip() + "\n"
        with open("output.txt", "w") as file:
            file.write(out)
