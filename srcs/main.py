# from map_parser import MapParser, ParsingError
# from map_display import MapDisplay
# from drone import Drone
from reverse_cost_bfs import ReverseCostBFS
from solver import Solver
# from solver import Solver
# from copy import deepcopy
# import questionary
# from pathlib import Path
from map import Hub, Connection, Map
from pprint import pprint

if (__name__ == "__main__"):
    start = Hub(
        name="start",
        coord=(-1, 1),
        zone_type="normal",
        max_drones=3
    )
    end = Hub(
        name="goal",
        coord=(2, 1),
        zone_type="normal",
        max_drones=1
    )
    path_a = Hub(
        name="path_a",
        coord=(1, 0),
        zone_type="normal",
        max_drones=1
    )
    path_b = Hub(
        name="path_b",
        coord=(1, 2),
        zone_type="priority",
        max_drones=1
    )
    junction = Hub(
        name="junction",
        coord=(0, 1),
        zone_type="normal",
        max_drones=1
    )
    map = Map(
        start=start,
        end=end,
        nb_drones=3,
        hubs=[start, end, path_a, path_b, junction],
        connections=[
            Connection(
                hubs=(junction, path_a),
            ),
            Connection(
                hubs=(end, path_a),
            ),
            Connection(
                hubs=(junction, path_b),
            ),
            Connection(
                hubs=(start, junction),
                max_link_capacity=1
            ),
            Connection(
                hubs=(end, path_b),
            )
        ]
    )
    paths = ReverseCostBFS(map).run()
    # for (key, value) in paths.items():
    #     print(key, end="\t")
    #     for path in value:
    #         print(path.src.name, path.cost, end=", ")
    #     print()
    if (not len(paths[map.start.name])):
        print("No path from start to end")
        exit(1)
    solve = Solver(map, paths).run()
    # pprint(solve)
    print(len(solve) - 1)
