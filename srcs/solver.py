from typing import Dict, List, TypeAlias
from reverse_cost_bfs import Path
from map import Map
from drone import Drone
from copy import deepcopy
from utils import Utils
import sys

State: TypeAlias = Dict[str, List[Drone]]


class Solver:
    def __init__(self, map: Map, paths: Dict[str, List[Path]]) -> None:
        self.map = map
        self.paths = paths
        self.drones = []
        for i in range(self.map.nb_drones):
            self.drones.append(Drone(f"D{i + 1}", self.map.start.name))

    def _is_path_valid(self, state: State, path: Path) -> bool:
        if (path.src.name == self.map.end.name or
                len(state[path.src.name]) < path.src.max_drones):
            return (True)
        return (False)

    def _compute_wait_time(self, state: State, best_path: Path):
        wait_cost = best_path.cost + len(state[best_path.src.name])
        try:
            next = self.paths[best_path.src.name][0].src
            con = Utils.get_connection(
                (best_path.src, next), self.map.connections)
            if (con is None):
                return (sys.maxsize)
            return (wait_cost - con.max_link_capacity)
        except IndexError:
            return (sys.maxsize)

    def run(self) -> List[State]:
        states: List[State] = []
        states.append({h.name: [] for h in self.map.hubs})
        states[0][self.map.start.name] = list(self.drones)
        tmp_state: State = states[0]
        while (len(tmp_state.get(self.map.end.name, [])) < self.map.nb_drones):
            for drone in self.drones:
                for idx, path in enumerate(self.paths[drone.location]):
                    if (not self._is_path_valid(tmp_state, path)):
                        continue
                    best_path = self.paths[drone.location][0]
                    if (idx != 0 and
                        self._compute_wait_time(tmp_state, best_path)
                            < path.cost):
                        continue
                    tmp_state[drone.location].remove(drone)
                    drone.location = path.src.name
                    tmp_state[path.src.name].append(drone)
                    break
            states.append(deepcopy(tmp_state))
        return (states)
