from enum import Enum


class MoveReason(Enum):
    UNKNOWN = "?"
    RANDOM = "R"
    BOXED = "B"
    CONTINUE = "C"
    FLOOD_FILL = "F"


class Position:
    def __init__(self, x, y, field_width, field_height):
        self.x = x
        self.y = y
        self.field_width = field_width
        self.field_height = field_height

    def clone(self):
        return Position(self.x, self.y, self.field_width, self.field_height)


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def rotate_ccw(self):
        if self == Direction.UP:
            return Direction.LEFT
        elif self == Direction.RIGHT:
            return Direction.UP
        elif self == Direction.DOWN:
            return Direction.RIGHT
        else:
            return Direction.DOWN

    def rotate_cw(self):
        if self == Direction.UP:
            return Direction.RIGHT
        elif self == Direction.RIGHT:
            return Direction.DOWN
        elif self == Direction.DOWN:
            return Direction.LEFT
        else:
            return Direction.UP

    def get_relative(self, to):
        if to == Direction.UP:
            return self
        elif to == Direction.RIGHT:
            return self.rotate_cw()
        elif to == Direction.LEFT:
            return self.rotate_ccw()
        else:
            return self.rotate_cw().rotate_cw()

    def from_position_absolute(self, pos: Position):
        new_pos = pos.clone()
        new_pos.x = self.get_x(pos.x, pos.field_width)
        new_pos.y = self.get_y(pos.y, pos.field_height)
        return new_pos

    def get_x(self, x: int, width: int):
        if self == Direction.UP or self == Direction.DOWN:
            return x
        if self == Direction.LEFT:
            return (x - 1) % width
        return (x + 1) % width

    def get_y(self, y: int, height: int):
        if self == Direction.LEFT or self == Direction.RIGHT:
            return y
        if self == Direction.UP:
            return (y - 1) % height
        return (y + 1) % height


class Path:
    def __init__(self, *directions: Direction):
        self.directions = list(directions)

    def resolve(self, arg_pos: Position) -> Position:
        pos = arg_pos.clone()
        for direction in self.directions:
            pos = direction.from_position_absolute(pos)
        return pos
