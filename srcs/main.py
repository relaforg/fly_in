from map_parser import MapParser
from map_display import MapDisplay
from reverse_cost_bfs import ReverseCostBFS
from solver import Solver
import questionary
from pathlib import Path
from utils import ParsingError
from sys import argv


def show_menu() -> str:
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
                return (str(obj.resolve()))
    except FileNotFoundError:
        print("Maps folder not found")
        exit(1)


if (__name__ == "__main__"):
    if (len(argv) > 2):
        print("Too many arguments")
        exit(1)
    elif (len(argv) == 2):
        file_path = argv[1]
    else:
        file_path = show_menu()
    try:
        map = MapParser(file_path).run()
    except ParsingError as e:
        print(e)
        exit(1)
    try:
        paths = ReverseCostBFS(map).run()
        if (not len(paths[map.start.name])):
            print("No path from start to end")
            exit(1)
        solve = Solver(map, paths).run()
        display = MapDisplay(map, solve)
        display.run()
        display.destroy()
    except Exception as e:
        print(e)
        exit(1)
