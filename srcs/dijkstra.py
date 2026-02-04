from map_parser import Map, Hub
from typing import List


class Dijkstra:
    def __init__(self, map: Map):
        self.map = map

    def _find_hub_by_name(self, hub_name: str) -> Hub | None:
        for h in self.map.hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    def _get_neighboors(self, hub: Hub) -> List[Hub]:
        n = []
        for c in hub.neighboors:
            tmp = self._find_hub_by_name(c.dst)
            if (tmp is not None):
                n.append(tmp)
        return (n)

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

    def _reverse(self, out):
        new = {}
        for src, edges in out.items():
            for (dst, cost) in edges:
                if (dst not in new):
                    new[dst] = []
                new[dst].append((src, cost))
        for (name, values) in new.items():
            values.sort(key=lambda c:
                        (c[1], 0 if self._find_hub_by_name(c[0]).zone_type ==
                         "priority" else 1))
        return (new)

    def run(self):
        visited = set()
        queue = [(self.map.end, 0)]
        out = {}

        while (len(queue)):
            current, cost = queue.pop(0)
            visited.add(current.name)
            neighboors = self._get_neighboors(current)
            if (not out.get(current.name)):
                out[current.name] = []
            for h in neighboors:
                # sauvegarder que si plus petit
                if (h.name not in visited and self._get_hub_cost(current) > 0):
                    new_cost = cost + \
                        self._get_hub_cost(self._find_hub_by_name(h.name))
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
