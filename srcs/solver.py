from typing import Dict, List, TypeAlias
from reverse_cost_bfs import Path
from map import Map, Connection, Hub
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

    def _is_not_fully_reserved(self, path: Path, connection: Connection,
                               reserved: Dict[str, List[int]],
                               current_hub: Hub) -> bool:
        # Test if drone is going toward a a restricted area
        if ("->" not in path.src.name):
            return (True)
        for hub in connection.hubs:
            if (hub.name != current_hub.name):
                dst = hub
                break
        if (len(reserved[dst.name]) < dst.max_drones):
            reserved[dst.name].append(0)
            return (True)
        return (False)

    def _is_path_valid(self, connection: Connection, state: State,
                       path: Path, con_used: Dict[str, List[Drone]],
                       reserved: Dict[str, List[int]],
                       current_hub: Hub) -> bool:
        if (path.src.name == self.map.end.name or
                (len(state[path.src.name]) < path.src.max_drones and
                 len(con_used[connection.name])
                 < connection.max_link_capacity
                 and self._is_not_fully_reserved(path, connection,
                                                 reserved, current_hub))):
            return (True)
        return (False)

    def _compute_wait_time(self, state: State, best_path: Path) -> int:
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

    def _get_current_connection(self, current_hub: Hub,
                                path: Path) -> Connection:
        current_con = Utils.get_connection(
            (current_hub, path.src), self.map.connections)
        if (current_con is not None):
            return (current_con)
        current_con = Utils.get_connection_by_name(
            path.src.name, self.map.connections)
        if (current_con is not None):
            return (current_con)
        exit(5)

    def _move_drone(self, tmp_state: State, path: Path, drone: Drone,
                    con_used: Dict[str, List[Drone]], conn_name: str) -> None:
        tmp_state[drone.location].remove(drone)
        drone.location = path.src.name
        tmp_state[path.src.name].append(drone)
        con_used[conn_name].append(drone)

    def _find_previous_location(self, state: State, drone_id: str) -> str:
        for (hub_name, drones) in state.items():
            for d in drones:
                if (d.id == drone_id):
                    return (hub_name)
        return ("")

    def _export_output(self, states: List[State]) -> None:
        try:
            with open("output.txt", "w") as file:
                for i in range(1, len(states)):
                    turn = ""
                    for (hub_name, drones) in states[i].items():
                        for d in drones:
                            if (hub_name != self._find_previous_location(
                                    states[i - 1], d.id)):
                                turn += f"{d.id}-{hub_name} "
                    file.write(turn.strip() + "\n")

        except Exception as e:
            print(e)

    def run(self) -> List[State]:
        states: List[State] = []
        hub_state: State = {h.name: [] for h in self.map.hubs}
        con_state: State = {c.name: [] for c in self.map.connections}
        states.append(hub_state | con_state)
        states[0][self.map.start.name] = list(self.drones)
        tmp_state: State = deepcopy(states[0])
        reserved: Dict[str, List[int]] = {
            h.name: [] for h in self.map.hubs if h.zone_type == "restricted"}
        while (len(tmp_state.get(self.map.end.name, [])) < self.map.nb_drones):
            con_used: Dict[str, List[Drone]] = {
                c.name: [] for c in self.map.connections}

            for drone in self.drones:
                current_hub = Utils.get_hub_by_name(
                    drone.location, self.map.hubs)

                # Drone is on a connection
                if (current_hub is None):
                    path = self.paths[drone.location][0]
                    reserved[path.src.name].pop()
                    self._move_drone(tmp_state, path, drone,
                                     con_used, drone.location)
                    continue

                for idx, path in enumerate(self.paths[drone.location]):
                    current_con = self._get_current_connection(
                        current_hub, path)
                    if (not self._is_path_valid(current_con, tmp_state, path,
                                                con_used, reserved,
                                                current_hub)):
                        continue
                    best_path = self.paths[drone.location][0]
                    if (idx != 0 and
                        self._compute_wait_time(tmp_state, best_path)
                            < path.cost):
                        continue
                    self._move_drone(tmp_state, path, drone,
                                     con_used, current_con.name)
                    break
            states.append(deepcopy(tmp_state))
        self._export_output(states)
        return (states)
