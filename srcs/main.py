from map_parser import MapParser, ParsingError
from map_display import MapDisplay
from drone import Drone
from dijkstra import Dijkstra
from solver import Solver
from copy import deepcopy
import questionary
from pathlib import Path

if (__name__ == "__main__"):
    try:
        p = Path("maps")
        while (True):
            choices = []
            path_by_label = {}
            for item in p.iterdir():
                if item.is_dir():
                    label = f"📁 {item.name}"
                    choices.append(label)
                    path_by_label[label] = item

                elif item.is_file() and item.suffix == ".txt":
                    label = f"📄 {item.name}"
                    choices.append(label)
                    path_by_label[label] = item
            label = questionary.select(
                "Select your map",
                choices=choices
            ).ask()
            obj = path_by_label[label]
            if (obj.is_dir()):
                p = obj.resolve()
            elif (obj.is_file()):
                file_path = obj.resolve()
                break
    except FileNotFoundError:
        print("Maps folder not found")
        exit(1)

    try:
        parser = MapParser(str(file_path))
        map = parser.extract()
        paths = Dijkstra(map).run()
        drones = []
        for d in range(map.nb_drones):
            drones.append(Drone(str(d + 1), map.start.coord))
        Solver(map, paths, deepcopy(drones)).run()
        display = MapDisplay(map, drones, "output.txt")
        display.run()
        display.destroy()
    except ParsingError as e:
        print(e)
