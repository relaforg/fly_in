from map_parser import Map, Hub
from font_monospace import FONT, FONT_W, FONT_H, NO_CHAR
from mlx import Mlx
from typing import Any, Tuple


class MapDisplay:
    def __init__(self, map: Map):
        self.map = map
        self.cell_size = 199
        self.offset = (0, 0)
        self.drag_start: Tuple[int, int] | None = None
        self.m = Mlx()
        self.mlx = self.m.mlx_init()
        self.win = self.m.mlx_new_window(
            self.mlx, 1080, 720, "Fly in - relaforg")
        self._compute_graph_info()
        self._compute_img()

    def _compute_graph_info(self):
        min_x = min(self.map.hubs, key=lambda x: x.coord[0]).coord[0]
        max_x = max(self.map.hubs, key=lambda x: x.coord[0]).coord[0]
        min_y = min(self.map.hubs, key=lambda x: x.coord[1]).coord[1]
        max_y = max(self.map.hubs, key=lambda x: x.coord[1]).coord[1]
        self.graph_size = (max_x - min_x + 1, max_y - min_y + 1)
        self.x_offset = -min(min_x, 0)
        self.y_offset = -min(min_y, 0)

    def _compute_img(self):
        self.img_width = self.graph_size[0] * self.cell_size
        self.img_height = self.graph_size[1] * self.cell_size
        self.img = self.m.mlx_new_image(
            self.mlx, self.img_width, self.img_height)
        self.addr, bpp, self.line_len, _ = self.m.mlx_get_data_addr(self.img)
        self.bpp = bpp // 8

    def run(self):
        self.m.mlx_hook(self.win, 33, 0,
                        lambda _: self.m.mlx_loop_exit(self.mlx), None)
        self.m.mlx_mouse_hook(self.win, self.on_mouse, None)
        self.m.mlx_hook(self.win, 5, 1 << 3, self.on_mouse_release, None)
        self.draw()
        self.refresh()
        self.m.mlx_loop(self.mlx)

    def draw(self):
        self.fill_img()
        self.put_border()
        for h in self.map.hubs:
            self.put_connections(h)
        for h in self.map.hubs:
            self.put_hub(h)

    def refresh(self) -> None:
        """Refresh the window to display modification
        """
        x: int = (1080 - self.img_width) // 2 + self.offset[0]
        y: int = (720 - self.img_height) // 2 + self.offset[1]
        self.m.mlx_clear_window(self.mlx, self.win)
        self.m.mlx_put_image_to_window(self.mlx, self.win, self.img, x, y)
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
            self.drag_start = (x, y)

    def _graph_to_img_coord(self, graph_x: int,
                            graph_y: int) -> Tuple[int, int]:
        return (((graph_x + self.x_offset) * self.cell_size)
                + self.cell_size // 2,
                ((graph_y + self.y_offset) * self.cell_size)
                + self.cell_size // 2)

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

    def put_border(self):
        for y in range(self.img_height):
            for x in range(self.img_width):
                if (x == 0 or y == 0 or x == self.img_width - 1
                        or y == self.img_height - 1):
                    self.put_pixel(x, y)

    def put_connections(self, hub: Hub) -> None:
        for c in hub.neighboors:
            h = [h for h in self.map.hubs if c.to == h.name][0]
            self.put_line(self._graph_to_img_coord(hub.coord[0], hub.coord[1]),
                          self._graph_to_img_coord(h.coord[0], h.coord[1]))

    def put_hub(self, hub: Hub):
        size = 7
        offset = size // 2
        for i in range(size):
            for j in range(size):
                x, y = self._graph_to_img_coord(hub.coord[0], hub.coord[1])
                color = self._color_to_hex(hub.color)
                self.put_pixel(x - offset + j, y - offset + i, color)
        offset_x = len(hub.name) * FONT_W // 2
        self._put_string(x - offset_x, y - size - FONT_H, hub.name)

    def fill_img(self, color: int = 0x000000FF) -> None:
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
        self.addr[:] = px * (self.img_width * self.img_height)

    def _put_string(self, x: int, y: int, string: str):
        for c in range(len(string)):
            self._put_letter(x + c * FONT_W, y, string[c])

    def _put_letter(self, x: int, y: int, letter: str) -> None:
        glyph = FONT.get(letter, NO_CHAR)
        for dy in range(len(glyph)):
            for dx in range(len(glyph[dy])):
                if (glyph[dy][dx] != 0):
                    self.put_pixel(x + dx, y + dy, 0xFFFFFF00 + glyph[dy][dx])

    def put_line(self, c1: Tuple[int, int], c2: Tuple[int, int]):
        dx = abs(c2[0] - c1[0])
        dy = abs(c2[1] - c1[1])
        sx = 1 if c1[0] < c2[0] else -1
        sy = 1 if c1[1] < c2[1] else -1
        err = dx - dy
        x0, y0 = c1
        x1, y1 = c2
        while True:
            self.put_pixel(x0, y0, 0xC0C0C0FF)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def put_pixel(self, x: int, y: int, color: int = 0xFFFFFFFF) -> None:
        """Put a pixel on the image

        Args:
        x, y: pixel coordinates
        color: The pixel color
        """
        if x < 0 or y < 0 or x >= self.img_width or y >= self.img_height:
            return
        offset = y * self.line_len + x * self.bpp

        self.addr[offset] = (color >> 8) & 0xFF
        self.addr[offset + 1] = (color >> 16) & 0xFF
        self.addr[offset + 2] = (color >> 24) & 0xFF
        self.addr[offset + 3] = color & 0xFF
