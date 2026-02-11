from map_parser import MapParser
from map_display import MapDisplay
from reverse_cost_bfs import ReverseCostBFS
from solver import Solver
# import questionary
# from pathlib import Path
from map import Hub, Connection
from utils import ParsingError
from pprint import pprint

if (__name__ == "__main__"):
    try:
        map = MapParser("maps/test2.txt").run()
        # print(map)
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
