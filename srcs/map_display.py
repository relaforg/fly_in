from map_parser import Map, Hub
from font_monospace import FONT, FONT_W, FONT_H, NO_CHAR
from mlx import Mlx
from typing import Any, Tuple, List
from drone import Drone
from time import monotonic


class Image:
    def __init__(self, m: Mlx, mlx: Any, width: int, height: int):
        self.img = m.mlx_new_image(mlx, width, height)
        self.addr, bpp, self.line_len, _ = m.mlx_get_data_addr(self.img)
        self.bpp = bpp // 8
        self.width = width
        self.height = height


class MapDisplay:
    def __init__(self, map: Map, drones: List[Drone]):
        self.map = map
        self.drones = drones
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
        self.current_hub: Hub | None = None

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

    def _graph_to_img_coord(self, graph_x: int,
                            graph_y: int) -> Tuple[int, int]:
        return (((graph_x + self.x_offset) * self.cell_size)
                + self.cell_size // 2,
                ((graph_y + self.y_offset) * self.cell_size)
                + self.cell_size // 2)

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
            case "white" | _:
                return (0xFFFFFFFF)

    def run(self):
        self.m.mlx_hook(self.win, 33, 0,
                        lambda _: self.m.mlx_loop_exit(self.mlx), None)
        self.m.mlx_mouse_hook(self.win, self.on_mouse, None)
        self.m.mlx_hook(self.win, 5, 1 << 3, self.on_mouse_release, None)
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

    def refresh(self) -> None:
        """Refresh the window to display modification
        """
        x: int = (1080 - self.img.width) // 2 + self.offset[0]
        y: int = (720 - self.img.height) // 2 + self.offset[1]
        self.m.mlx_clear_window(self.mlx, self.win)
        self.m.mlx_put_image_to_window(self.mlx, self.win, self.img.img, x, y)
        if (self.modal is not None):
            if (self.current_hub is not None):
                x, y = self._graph_to_img_coord(self.current_hub.coord[0],
                                                self.current_hub.coord[1])
                x, y = self._img_to_win_coord(x, y)
            self.m.mlx_put_image_to_window(
                self.mlx, self.win, self.modal.img,
                x - (self.modal.width // 2), y + 10)
        self.m.mlx_string_put(self.mlx, self.win, 15, 10, 0xFFFFFFFF,
                              "Fly in")

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
                if (h is not None):
                    self.current_hub = h
                    self.put_hub_info(h)
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

    def put_hub_info(self, hub: Hub):
        if (self.modal is not None):
            self.m.mlx_destroy_image(self.mlx, self.modal.img)
            # potential refresh here
        display: List[str] = [hub.name, "zone_type: " + hub.zone_type,
                              "max_drones: " + str(hub.max_drones)]
        drones = [d.id for d in self.drones if d.coord == hub.coord]
        display += drones
        print(display)
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

    def put_connections(self, hub: Hub) -> None:
        for c in hub.neighboors:
            h = [h for h in self.map.hubs if c.to == h.name][0]
            self.put_line(self.img,
                          self._graph_to_img_coord(hub.coord[0], hub.coord[1]),
                          self._graph_to_img_coord(h.coord[0], h.coord[1]))

    def put_hub(self, hub: Hub):
        x, y = self._graph_to_img_coord(hub.coord[0], hub.coord[1])
        size = 7
        offset = size // 2
        for i in range(size):
            for j in range(size):
                color = self._color_to_hex(hub.color)
                self.put_pixel(self.img, x - offset + j, y - offset + i, color)
        offset_x = len(hub.name) * FONT_W // 2
        self.put_string(self.img, x - offset_x, y - size - FONT_H, hub.name)
        nb_drone = len([d for d in self.drones if d.coord == hub.coord])
        if (nb_drone != 0):
            self.put_string(self.img, x + 3, y + size + 5, str(nb_drone))
            self.put_drone(x - 15, y + 10)

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
