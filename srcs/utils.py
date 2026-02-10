from map import Hub, Connection, List
from typing import Tuple
from collections import Counter


class Utils:
    @staticmethod
    def get_hub_travel_cost(hub: Hub) -> int:
        match hub.zone_type:
            case "normal" | "priority":
                return (1)
            case "restricted":
                return (2)
            case _:
                return (-1)

    @staticmethod
    def get_connection(couple: Tuple[Hub, Hub],
                       connections: List[Connection]) -> Connection | None:
        for c in connections:
            if (Counter((h.name for h in couple))
                    == Counter((h.name for h in c.hubs))):
                return (c)
        return (None)

    @staticmethod
    def get_hub_by_name(hub_name: str, hubs: List[Hub]) -> Hub | None:
        for h in hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    @staticmethod
    def get_connection_by_name(con_name: str, connections: List[Connection]) \
            -> Connection | None:
        for c in connections:
            if (c.name == con_name):
                return (c)
        return (None)
