from map_parser import Map, Hub
from typing import List, Dict, Tuple


class Dijkstra:
    """ Dijkstra alg class

    Attributes:
        map: Map
    """

    def __init__(self, map: Map):
        self.map = map

    def _find_hub_by_name(self, hub_name: str) -> Hub | None:
        """Find a hub object with his name

        Args:
            hub_name: str

        Returns:
            Hub if found
            None if not
        """
        for h in self.map.hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    def _get_neighboors(self, hub: Hub) -> List[Hub]:
        """ Returns existing hubs object neighboors

        Args:
            hub: Hub

        Returns:
            List of hubs
        """
        n = []
        for c in hub.neighboors:
            tmp = self._find_hub_by_name(c.dst)
            if (tmp is not None):
                n.append(tmp)
        return (n)

    def _get_hub_cost(self, hub: Hub) -> int:
        """Get hub cost

        Args:
            hub: Hub

        Returns:
            int - the hub cost
        """
        match hub.zone_type:
            case "normal":
                return (1)
            case "restricted":
                return (2)
            case "priority":
                return (1)
            case "blocked":
                return (-1)
            case _:
                return (10)

    def _priority_key(self, edge: Tuple[str, int]) -> Tuple[int, int]:
        """Compute sorting key

        Args:
            edge: Tuple[str, int]

        Returns:
            Tuple[int, int] - cost and 1 if priority else 0
        """
        dst, cost = edge
        hub = self._find_hub_by_name(dst)
        if hub is None:
            return (cost, 1)
        return (cost, 0 if hub.zone_type == "priority" else 1)

    def _reverse(self, out: Dict[str, List[Tuple[str, int]]]) \
            -> Dict[str, List[Tuple[str, int]]]:
        """Reverse a Dijkstra dict

        Args:
            out: Dict

        Returns:
            Dict
        """
        new: Dict[str, List[Tuple[str, int]]] = {}
        for src, edges in out.items():
            for (dst, cost) in edges:
                if (dst not in new):
                    new[dst] = []
                new[dst].append((src, cost))
        for (name, values) in new.items():
            values.sort(key=self._priority_key)
        return (new)

    def run(self) -> Dict[str, List[Tuple[str, int]]]:
        """Run the dijkstra algorithm

        Returns:
            Dict
        """
        visited = set()
        queue = [(self.map.end, 0)]
        out: Dict[str, List[Tuple[str, int]]] = {}

        while (len(queue)):
            current, cost = queue.pop(0)
            visited.add(current.name)
            neighboors = self._get_neighboors(current)
            if (not out.get(current.name)):
                out[current.name] = []
            for h in neighboors:
                if (h.name not in visited and self._get_hub_cost(current) > 0):
                    tmp = self._find_hub_by_name(h.name)
                    if (tmp is None):
                        continue
                    new_cost = cost + self._get_hub_cost(tmp)
                    for i in range(len(out[current.name])):
                        if (h.name == out[current.name][i][0]):
                            if (new_cost < out[current.name][i][1]):
                                out[current.name].pop(i)
                                out[current.name].append((h.name, new_cost))
                            break
                    else:
                        out[current.name].append((h.name, new_cost))
                    queue.append((h, new_cost))
        return (self._reverse(out))
