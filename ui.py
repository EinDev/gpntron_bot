from multiprocessing import Queue
from tkinter import *
from typing import Union

from util import Direction

COLORS = ["#e6b0aa", "#c39bd3", "#7fb3d5", "#48c9b0", "#52be80", "#f4d03f", "#f5b041", "#dc7633", "green", "yellow", "blue", "magenta", "cyan"]

class GUI(Tk):
    def __init__(self, x: int, y: int):
        Tk.__init__(self)
        self._grid_size = 20
        self._size = (x,y)
        width = x * self._grid_size
        height = y * self._grid_size
        self.geometry(f'{width}x{height}')
        self.resizable(False, False)

        self.canvas = Canvas(self, bg='white', width=width, height=height)
        self.canvas.pack()
        self.queue = Queue()

    def update_game(self, player_heads: dict[int, tuple[int, int]], grid: list[int,list[int, Union[int, None]]],
                    own_pid: int, could_collide: set[Direction], move_dir: Direction,
                    move_reasons: list[int,list[int, Union[int, None]]]):
        self.canvas.delete('all')
        self._draw_grid(*self._size)

        print(len(could_collide))

        grid_size = len(grid)
        x = 0
        for xvals in grid:
            y = 0
            for pid in xvals:
                if pid is not None:
                    self.canvas.create_rectangle(x, y, x+self._grid_size, y+self._grid_size, fill=COLORS[pid % len(COLORS)])
                y += self._grid_size
            x += self._grid_size

        x = 0
        for xvals in move_reasons:
            y = 0
            for reason in xvals:
                if reason is not None:
                    self.canvas.create_text(x + self._grid_size/2, y + self._grid_size/1.5, text=reason, fill="black", font=(f'Helvetica {int(self._grid_size/1.5)} bold'))
                y += self._grid_size
            x += self._grid_size

        for (pid, pos) in player_heads.items():
            x = pos[0]
            y = pos[1]
            if pid == own_pid:
                self.draw_x(x, y, "red")
                self.draw_x(move_dir.get_x(x, grid_size), move_dir.get_y(y, grid_size), "red")
                for direc in could_collide:
                    self.draw_x(direc.get_x(pos[0], grid_size), direc.get_y(pos[1], grid_size), "gray")
            else:
                self.draw_x(x, y, "white")
        self.update()

    def draw_x(self, x, y, color):
        x = x * self._grid_size
        y = y * self._grid_size
        self.canvas.create_line(x, y, x + self._grid_size, y + self._grid_size, fill=color, width=2)
        self.canvas.create_line(x, y + self._grid_size, x + self._grid_size, y, fill=color, width=2)

    def _draw_grid(self, x, y):
        for i in range(1, x):
            pos = i * self._grid_size
            self.canvas.create_line(pos, 0, pos, y * self._grid_size, width=1, fill="lightgray")
        for i in range(1, y):
            pos = i * self._grid_size
            self.canvas.create_line(0, pos, x * self._grid_size, pos, width=1, fill="lightgray")

