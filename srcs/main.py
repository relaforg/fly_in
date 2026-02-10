from map_parser import MapParser
from map_display import MapDisplay
# from drone import Drone
from reverse_cost_bfs import ReverseCostBFS
from solver import Solver
# from solver import Solver
# from copy import deepcopy
# import questionary
# from pathlib import Path
from map import Hub, Connection, Map
from utils import ParsingError

if (__name__ == "__main__"):
    try:
        map = MapParser("maps/easy/02_simple_fork.txt").run()
        print(map)
    except ParsingError as e:
        print(e)
    paths = ReverseCostBFS(map).run()
    if (not len(paths[map.start.name])):
        print("No path from start to end")
        exit(1)
    solve = Solver(map, paths).run()
    display = MapDisplay(map, solve)
    display.run()
    display.destroy()
