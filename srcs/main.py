from map_parser import MapParser, ParsingError
from map_display import MapDisplay
from drone import Drone
from dijkstra import Dijkstra
from solver import Solver
from copy import deepcopy

if (__name__ == "__main__"):
    parser = MapParser("maps/easy/02_simple_fork.txt")
    try:
        map = parser.extract()
        paths = Dijkstra(map).run()
        drones = []
        for d in range(map.nb_drones):
            drones.append(Drone(str(d + 1), map.start.coord))
        Solver(map, paths, deepcopy(drones)).run()
        display = MapDisplay(map, drones, "output.txt")
        display.run()
    except ParsingError as e:
        print(e)
