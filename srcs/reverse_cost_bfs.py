from map import Map, Hub
from typing import Dict, List
from dataclasses import dataclass
from utils import Utils


@dataclass
class Path:
    src: Hub
    cost: int


class ReverseCostBFS():
    """Graph path mapping class

    Attributes:
        map: Map
    """

    def __init__(self, map: Map) -> None:
        self.map = map

    def _get_neighboors(self, hub: Hub) -> List[Hub]:
        """Get all neighbooring hub

        Args:
            hub: Hub

        Returns:
            List[Hub]
        """
        neighboors: List[Hub] = []
        for c in self.map.connections:
            if (hub in c.hubs):
                neighboors.append([n for n in c.hubs if n != hub][0])
        return (neighboors)

    def _save_path(self, dst: Hub, paths: Dict[str, List[Path]],
                   path: Path) -> None:
        """Save the better path

        Args:
            dst: Hub
            paths: Dict[str, list[Path]]
            path: Path
        """
        # If I already have a path from path.src I save the best one
        if (path.src.name in [p.src.name for p in paths[dst.name]]):
            for p in paths[dst.name]:
                if (p.src.name == path.src.name and p.cost > path.cost):
                    p.cost = path.cost
        else:
            if (path.src.zone_type == "restricted"):
                con = Utils.get_connection(
                    (dst, path.src), self.map.connections)
                if (con is None):
                    return
                paths[con.name] = [path]
                paths[dst.name].append(Path(
                    Hub(name=con.name,
                        coord=(-1, -1),
                        max_drones=con.max_link_capacity
                        ), path.cost + 1))
            else:
                paths[dst.name].append(path)

    def _sort_paths(self, paths: Dict[str, List[Path]]) -> None:
        """Sort path by cost and then priority

        Args:
            paths: Dict[str, List[Path]]
        """
        for path_list in paths.values():
            path_list.sort(key=lambda p: (
                p.cost, p.src.zone_type != "priority"))

    def run(self) -> Dict[str, List[Path]]:
        """Run the graph mapping algorithm

        Returns:
            Dict[str, List[Path]]
        """
        paths: Dict[str, List[Path]] = {n.name: [] for n in self.map.hubs}
        queue: List[Path] = [Path(self.map.end, 0)]
        visited = set()

        while (len(queue) > 0):
            path = queue.pop(0)
            for n in self._get_neighboors(path.src):
                # To prevent path going backward and going onto blocked hub
                if (n.name in visited or Utils.get_hub_travel_cost(n) < 0):
                    continue
                self._save_path(n, paths, path)
                if (path.src.name not in visited):
                    queue.append(
                        Path(n, path.cost + 1))
            visited.add(path.src.name)
            self._sort_paths(paths)
        return (paths)
