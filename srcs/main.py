from map_parser import MapParser, ParsingError
from map_display import MapDisplay

if (__name__ == "__main__"):
    parser = MapParser("maps/easy/02_simple_fork.txt")
    try:
        map = parser.extract()
        print(map)
        display = MapDisplay(map)
        display.run()
    except ParsingError as e:
        print(e)
