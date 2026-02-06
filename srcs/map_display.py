from map_parser import Map, Hub, Connection
from font_monospace import FONT, FONT_W, FONT_H, NO_CHAR
from mlx import Mlx
from typing import Any, Tuple, List, TypedDict
from drone import Drone
from time import monotonic
from copy import deepcopy
from math import ceil
from random import randint


class ConnCoord(TypedDict):
    coord: tuple[int, int]
    conn: Connection


class Image:
    def __init__(self, m: Mlx, mlx: Any, width: int, height: int):
        self.img = m.mlx_new_image(mlx, width, height)
        self.addr, bpp, self.line_len, _ = m.mlx_get_data_addr(self.img)
        self.bpp = bpp // 8
        self.width = width
        self.height = height


class MapDisplay:
    def __init__(self, map: Map, drones: List[Drone], output_path: str):
        self.map = map
        self.drones_state = [deepcopy(drones)]
        self._extract_output(output_path)
        self.cell_size = 199
        self.offset = (0, 0)
        self.drag_start: Tuple[int, int] | None = None
        self.m = Mlx()
        self.mlx = self.m.mlx_init()
        self.win = self.m.mlx_new_window(
            self.mlx, 1080, 720, "Fly in - relaforg")
        self._compute_graph_info()
        self.img = Image(self.m, self.mlx, self.graph_size[0] * self.cell_size,
                         self.graph_size[1] * self.cell_size)
        self.last_click = monotonic()
        self.modal: None | Image = None
        # self.current_hub: Hub | None = None
        self.current_modal_coord: Tuple[int, int] | None = None
        self.step = 0
        self.conn_coord: List[ConnCoord] = []

    def _compute_graph_info(self):
        min_x = min(self.map.hubs, key=lambda x: x.coord[0]).coord[0]
        max_x = max(self.map.hubs, key=lambda x: x.coord[0]).coord[0]
        min_y = min(self.map.hubs, key=lambda x: x.coord[1]).coord[1]
        max_y = max(self.map.hubs, key=lambda x: x.coord[1]).coord[1]
        self.graph_size = (max_x - min_x + 1, max_y - min_y + 1)
        self.x_offset = -min(min_x, 0)
        self.y_offset = -min(min_y, 0)

    def _compute_img(self):
        self.img_height = self.graph_size[1] * self.cell_size

    def _find_hub_by_name(self, hub_name: str) -> Hub | None:
        for h in self.map.hubs:
            if (h.name == hub_name):
                return (h)
        return (None)

    def _extract_output(self, output_path: str) -> None:
        try:
            with open(output_path, "r") as file:
                lines = list(file)
                nbr_line = len(lines)
        except FileNotFoundError:
            raise FileNotFoundError(f"{output_path} does not exists")
        except PermissionError:
            raise PermissionError(
                f"You do not have read permission on {output_path}")
        hub_coord_by_name = {h.name: h.coord for h in self.map.hubs}
        for line_idx in range(nbr_line):
            state = deepcopy(self.drones_state[line_idx])
            drone_by_id = {d.id: d for d in state}
            for token in lines[line_idx].split():
                raw_id, hub_name = token.split("-", 1)
                drone_id = raw_id[1:]
                d = drone_by_id.get(drone_id)
                coord = hub_coord_by_name.get(hub_name)
                if d is not None and coord is not None:
                    d.coord = coord
                elif d is not None:
                    if "->" not in hub_name:
                        continue
                    src_name, dst_name = hub_name.split("->", 1)
                    src_coord = hub_coord_by_name.get(src_name)
                    dst_coord = hub_coord_by_name.get(dst_name)
                    if src_coord is None or dst_coord is None:
                        continue
                    mx = (src_coord[0] + dst_coord[0]) / 2
                    my = (src_coord[1] + dst_coord[1]) / 2
                    d.coord = (mx, my)
                else:
                    continue

            self.drones_state.append(state)

    def _graph_to_img_coord(self, graph_x: int,
                            graph_y: int) -> Tuple[int, int]:
        return (ceil(((graph_x + self.x_offset) * self.cell_size)
                + self.cell_size // 2),
                ceil(((graph_y + self.y_offset) * self.cell_size)
                + self.cell_size // 2))

    def _win_to_img_coord(self, win_x: int, win_y: int) -> Tuple[int, int]:
        x: int = -((1080 - self.img.width) // 2 + self.offset[0] - win_x)
        y: int = -((720 - self.img.height) // 2 + self.offset[1] - win_y)
        return (x, y)

    def _img_to_win_coord(self, img_x: int, img_y: int) -> Tuple[int, int]:
        map_x = (1080 - self.img.width) // 2 + self.offset[0]
        map_y = (720 - self.img.height) // 2 + self.offset[1]
        return (map_x + img_x, map_y + img_y)

    def _color_to_hex(self, color: str):
        match color:
            case "green":
                return (0x00FF00FF)
            case "red":
                return (0xFF0000FF)
            case "blue":
                return (0x0000FFFF)
            case "yellow":
                return (0xFFFF00FF)
            case "orange":
                return (0xFFA500FF)
            case "cyan":
                return (0x00FFFFFF)
            case "purple":
                return (0x800080FF)
            case "brown":
                return (0xD2691EFF)
            case "lime":
                return (0x32CD32FF)
            case "magenta":
                return (0xFF00FFFF)
            case "gold":
                return (0xFFD700FF)
            case "black":
                return (0x101010FF)
            case "maroon":
                return (0x800000FF)
            case "darkred":
                return (0x990000FF)
            case "violet":
                return (0x9400D3FF)
            case "crimson":
                return (0xDC143CFF)
            case "rainbow":
                return ((randint(0, 0xFFFFFF) << 8) | 0xFF)
            case "white" | _:
                print(color)
                return (0xFFFFFFFF)

    def run(self):
        self.m.mlx_hook(self.win, 33, 0,
                        lambda _: self.m.mlx_loop_exit(self.mlx), None)
        self.m.mlx_mouse_hook(self.win, self.on_mouse, None)
        self.m.mlx_hook(self.win, 5, 1 << 3, self.on_mouse_release, None)
        self.m.mlx_key_hook(self.win, self.key_pressed, None)
        self.draw()
        self.refresh()
        self.m.mlx_loop(self.mlx)

    def draw(self):
        self.fill_img(self.img)
        self.put_border(self.img)
        for h in self.map.hubs:
            self.put_connections(h)
        for h in self.map.hubs:
            self.put_hub(h)
        self.put_drones()

    def refresh(self) -> None:
        """Refresh the window to display modification
        """
        x: int = (1080 - self.img.width) // 2 + self.offset[0]
        y: int = (720 - self.img.height) // 2 + self.offset[1]
        self.m.mlx_clear_window(self.mlx, self.win)
        self.m.mlx_put_image_to_window(self.mlx, self.win, self.img.img, x, y)
        if (self.modal is not None):
            # if (self.current_hub is not None):
            if (self.current_modal_coord is not None):
                # x, y = self._graph_to_img_coord(self.current_modal_coord[0],
                #                                 self.current_modal_coord[1])
                x, y = self._img_to_win_coord(self.current_modal_coord[0],
                                              self.current_modal_coord[1])
            self.m.mlx_put_image_to_window(
                self.mlx, self.win, self.modal.img,
                x - (self.modal.width // 2), y + 10)
        self.m.mlx_string_put(self.mlx, self.win, 15, 10, 0xFFFFFFFF,
                              "Fly in")

    def key_pressed(self, keycode: int, _: Any) -> None:
        """Key press handler

        Args:
        keycode: which key has been pressed
        """
        if (keycode == 65363):
            if (self.step < len(self.drones_state) - 1):
                self.step += 1
                self.draw()
                self.refresh()
        elif (keycode == 65361):
            if (self.step > 0):
                self.step -= 1
                self.draw()
                self.refresh()
        elif (keycode == 113):
            self.m.mlx_loop_exit(self.mlx)

    def on_mouse_release(self, button: int, x: int, y: int, _: Any) -> None:
        """Mouse click release handler

        Args:
        button: which button is released
        x, y: release coordinates
        """
        if (self.drag_start and button == 1):
            self.offset = (self.offset[0] + x - self.drag_start[0],
                           self.offset[1] + y - self.drag_start[1])
            self.refresh()
            self.drag_start = None

    def on_mouse(self, button: int, x: int, y: int, _: Any) -> None:
        """Mouse click handler

        Args:
        button: which button is clicked
        x, y: click coordinates
        """
        if (button == 1):
            tmp = monotonic()
            if (tmp - self.last_click <= 0.3):
                x1, y1 = self._win_to_img_coord(x, y)
                h = self.get_hub_double_click(x1, y1)
                c = self.get_conn_double_click(x1, y1)
                if (h is not None):
                    self.current_modal_coord = \
                        self._graph_to_img_coord(h.coord[0], h.coord[1])
                    self.put_hub_info(h)
                elif (c is not None):
                    self.current_modal_coord = c["coord"]
                    self.put_conn_info(c["conn"])
            self.drag_start = (x, y)
            self.last_click = tmp
        elif (button == 3):
            if (self.modal is not None):
                self.m.mlx_destroy_image(self.mlx, self.modal.img)
                self.modal = None
                self.refresh()

    def get_hub_double_click(self, x: int, y: int) -> Hub | None:
        for h in self.map.hubs:
            x2, y2 = self._graph_to_img_coord(h.coord[0], h.coord[1])
            if (x <= x2 + 5 and x >= x2 - 5 and y <= y2 + 5 and y >= y2 - 5):
                return (h)
        return (None)

    def get_conn_double_click(self, x: int, y: int) -> ConnCoord | None:
        for c in self.conn_coord:
            x2, y2 = c["coord"]
            if (x <= x2 + 9 and x >= x2 - 9 and y <= y2 + 5 and y >= y2 - 5):
                return (c)
        return (None)

    def put_hub_info(self, hub: Hub):
        if (self.modal is not None):
            self.m.mlx_destroy_image(self.mlx, self.modal.img)
            # potential refresh here
        display: List[str] = [hub.name, "zone_type: " + hub.zone_type,
                              "max_drones: " + str(hub.max_drones)]
        drones = [d.id for d in self.drones_state[self.step]
                  if d.coord == hub.coord]
        display += drones
        offset = 1 if len(drones) else 0
        height = (5 + len(drones) + offset) * FONT_H
        width = (len(max(display, key=lambda d: len(d))) + 2) * FONT_W
        self.modal = Image(self.m, self.mlx, width, height)
        self.fill_img(self.modal)
        y = 10
        for i in range(len(display)):
            x = 5
            if (i == 0):
                x = width // 2 - len(display[i]) * FONT_W // 2
            if (i == 1 or i == 3):
                y += FONT_H
            self.put_string(self.modal, x, y, display[i])
            y += FONT_H
        self.put_border(self.modal)

    def put_conn_info(self, conn: Connection):
        if (self.modal is not None):
            self.m.mlx_destroy_image(self.mlx, self.modal.img)
            # potential refresh here
        display: List[str] = [f"max link capacity = {conn.max_link_capacity}"]
        height = (1) * FONT_H + 15
        width = (len(max(display, key=lambda d: len(d))) + 2) * FONT_W
        self.modal = Image(self.m, self.mlx, width, height)
        self.fill_img(self.modal)
        y = 10
        for i in range(len(display)):
            x = 5
            self.put_string(self.modal, x, y, display[i])
            y += FONT_H
        self.put_border(self.modal)

    def put_border(self, img: Image):
        for y in range(img.height):
            for x in range(img.width):
                if (x == 0 or y == 0 or x == img.width - 1
                        or y == img.height - 1):
                    self.put_pixel(img, x, y)

    def put_drone(self, x: int, y: int) -> None:
        for dy in range(len(Drone.glyph())):
            for dx in range(len(Drone.glyph()[dy])):
                if (Drone.glyph()[dy][dx] == 1):
                    self.put_pixel(self.img, x + dx, y + dy)

    def put_drones(self):
        nbr = {}
        for d in self.drones_state[self.step]:
            if (nbr.get(d.coord)):
                nbr[d.coord] += 1
            else:
                nbr[d.coord] = 1
        for (coord, nb_drone) in nbr.items():
            x, y = self._graph_to_img_coord(coord[0], coord[1])
            self.put_string(self.img, x + 3, y + 7 + 5, str(nb_drone))
            self.put_drone(x - 15, y + 10)

    def put_connections(self, hub: Hub) -> None:
        for c in hub.neighboors:
            h = [h for h in self.map.hubs if c.dst == h.name][0]
            coord_hub = self._graph_to_img_coord(hub.coord[0], hub.coord[1])
            coord_h = self._graph_to_img_coord(h.coord[0], h.coord[1])
            self.put_line(self.img, coord_hub, coord_h)
            mx = (coord_hub[0] + coord_h[0]) // 2
            my = (coord_hub[1] + coord_h[1]) // 2
            self.put_rect(mx - 7, my - 3, 15, 7)
            self.conn_coord.append({
                "conn": c,
                "coord": (mx, my)
            })

    def put_square(self, x: int, y: int, size: int,
                   color: int = 0xFFFFFFFF) -> None:
        for dy in range(size):
            for dx in range(size):
                self.put_pixel(self.img, x + dx, y + dy, color)

    def put_rect(self, x: int, y: int, width: int, height: int,
                 color: int = 0xFFFFFFFF) -> None:
        for dy in range(height):
            for dx in range(width):
                self.put_pixel(self.img, x + dx, y + dy, color)

    def put_hub(self, hub: Hub):
        x, y = self._graph_to_img_coord(hub.coord[0], hub.coord[1])
        size = 7
        offset = size // 2
        color = self._color_to_hex(hub.color)
        self.put_square(x - offset, y - offset, size, color)
        offset_x = len(hub.name) * FONT_W // 2
        self.put_string(self.img, x - offset_x,
                        y - size - FONT_H, hub.name)

    def fill_img(self, img: Image, color: int = 0x000000FF) -> None:
        """Fill an mlx image with color

        Args:
        color: The color with which the img will be filled
        """
        px = bytes((
            (color >> 8) & 0xFF,
            (color >> 16) & 0xFF,
            (color >> 24) & 0xFF,
            color & 0xFF,
        ))
        img.addr[:] = px * (img.width * img.height)

    def put_string(self, img: Image, x: int, y: int, string: str):
        for c in range(len(string)):
            self.put_letter(img, x + c * FONT_W, y, string[c])

    def put_letter(self, img: Image, x: int, y: int, letter: str) -> None:
        glyph = FONT.get(letter, NO_CHAR)
        for dy in range(len(glyph)):
            for dx in range(len(glyph[dy])):
                if (glyph[dy][dx] != 0):
                    self.put_pixel(img, x + dx, y + dy,
                                   0xFFFFFF00 + glyph[dy][dx])

    def put_line(self, img: Image, c1: Tuple[int, int], c2: Tuple[int, int]):
        dx = abs(c2[0] - c1[0])
        dy = abs(c2[1] - c1[1])
        sx = 1 if c1[0] < c2[0] else -1
        sy = 1 if c1[1] < c2[1] else -1
        err = dx - dy
        x0, y0 = c1
        x1, y1 = c2
        while (x0 != x1 or y0 != y1):
            self.put_pixel(img, x0, y0, 0xC0C0C0FF)
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def put_pixel(self, img: Image, x: int, y: int,
                  color: int = 0xFFFFFFFF) -> None:
        """Put a pixel on the image

        Args:
        x, y: pixel coordinates
        color: The pixel color
        """
        if x < 0 or y < 0 or x >= img.width or y >= img.height:
            return
        offset = y * img.line_len + x * img.bpp

        img.addr[offset] = (color >> 8) & 0xFF
        img.addr[offset + 1] = (color >> 16) & 0xFF
        img.addr[offset + 2] = (color >> 24) & 0xFF
        img.addr[offset + 3] = color & 0xFF
