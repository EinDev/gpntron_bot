import queue
import random
from typing import Optional

from util import Direction, MoveReason, Path, Position
from ui import GUI


class FieldCountAlgo:
    def count_fields(self, field: list[list[int]], x: int, y: int, width: int, height: int) -> dict[Direction, int]:
        self.already_counted = []
        self.field = field
        self.width = width
        self.height = height
        choices = {}
        for chosen_dir in Direction:
            choices[chosen_dir] = self._count_neighbors(chosen_dir.get_x(x, width), chosen_dir.get_y(y, height))
        return choices

    ###
    # Flood-fill (node):
    #   1. Set Q to the empty queue or stack.
    #   2. Add node to the end of Q.
    #   3. While Q is not empty:
    #   4.   Set n equal to the first element of Q.
    #   5.   Remove first element from Q.
    #   6.   If n is Inside:
    #          Set the n
    #          Add the node to the west of n to the end of Q.
    #          Add the node to the east of n to the end of Q.
    #          Add the node to the north of n to the end of Q.
    #          Add the node to the south of n to the end of Q.
    #   7. Continue looping until Q is exhausted.
    #   8. Return.

    @staticmethod
    def flood_fill_count(field: list[list[int]], x: int, y: int, width: int, height: int,
                         player_positions: dict[int, list[int]]):
        q = queue.Queue()
        q.put((x, y))
        num_fields = 0
        player_count = 0
        already_checked = []
        while not q.empty():
            n = q.get()
            if field[n[0]][n[1]] is None:
                num_fields += 1
                for direc in Direction:
                    new_x = direc.get_x(n[0], width)
                    new_y = direc.get_y(n[1], height)
                    coords_hash = new_x + new_y * width
                    if coords_hash not in already_checked:
                        q.put([new_x, new_y])
                        already_checked.append(coords_hash)
            else:
                if n in player_positions.values():
                    player_count += 1
        return num_fields, player_count

    def _count_neighbors(self, x: int, y: int) -> int:
        num = 0
        for chosen_dir in Direction:
            new_x = chosen_dir.get_x(x, self.width)
            new_y = chosen_dir.get_y(y, self.height)
            if self._is_countable(new_x, new_y):
                self.already_counted.append("%i|%i" % (new_x, new_y))
                num += 1
                num += self._count_neighbors(new_x, new_y)
            else:
                print("field at %i/%i is not countable!" % (new_x, new_y))
        return num

    def _is_countable(self, x: int, y: int):
        if "%i|%i" % (x, y) in self.already_counted:
            return False
        return self.field[x][y] is None


class GameState:
    def __init__(self, width: int, height: int, own_playerid: int):
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(own_playerid, int)
        self._own_playerid = own_playerid
        self._game_width = width
        self._game_height = height
        self._grid = [[None] * height for _ in range(width)]
        self._current_dir = Direction.UP
        self._last_positions = {}
        self._field_count = FieldCountAlgo()
        self._last_message_tick = 0
        self.boxed_in = False
        self._tick = 0
        self._ui = GUI(self._game_width, self._game_height)
        self._move_reasons = [[None] * height for _ in range(width)]


    def update_player_pos(self, playerid: int, pos_x: int, pos_y: int):
        # assert self._grid[pos_x][pos_y] is None
        self._grid[pos_x][pos_y] = playerid
        self._last_positions[playerid] = [pos_x, pos_y]

    def _will_collide(self, dir: Direction):
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        field = self._get_field_at(pos_x, pos_y, dir)
        print("Field at %i/%i at dir %s is %s" % (pos_x, pos_y, dir.value, str(field)))
        return field is not None

    def _get_player_at(self, x: int, y: int):
        for key, val in self._last_positions.items():
            if val == [x, y]:
                return key
        return None

    def _is_player_at(self, x: int, y: int):
        return self._get_player_at(x, y) not in [None, self._own_playerid]

    def _is_player_near(self, x: int, y: int):
        return True in [
            self._is_player_at(d.get_x(x, self._game_width), d.get_y(y, self._game_height))
            for d in Direction
        ]

    def get_own_pos(self):
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        return Position(pos_x, pos_y, self._game_width, self._game_height)

    def should_do_floodfill(self):
        floodfill_check_fields = [
            Path(Direction.LEFT, Direction.UP), Path(Direction.RIGHT, Direction.UP),
            Path(Direction.LEFT, Direction.DOWN), Path(Direction.RIGHT, Direction.DOWN),
        ]
        fields = [
            self._grid[resolved.x][resolved.y] is not None for resolved in [path.resolve(self.get_own_pos()) for path in floodfill_check_fields]
        ]
        fields_set = 0
        for field in fields:
            if field:
                fields_set += 1
        return fields_set >= 2
    def get_move(self, stick: int) -> Optional[tuple[Direction, str]]:
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        max_fields = 0
        max_dir = Direction.UP
        move_reason = MoveReason.UNKNOWN
        max_players = 0
        message = None
        dirs = [d for d in Direction]
        self._tick += 1
        if not self.boxed_in and self._tick % 5 == 0:
            random.shuffle(dirs)
        # last_char = getchar()
        last_char = None
        print(f"using preferred key {last_char}")
        if last_char == "w":
            dirs = [Direction.UP, *dirs]
        elif last_char == "a":
            dirs = [Direction.LEFT, *dirs]
        elif last_char == "s":
            dirs = [Direction.DOWN, *dirs]
        elif last_char == "d":
            dirs = [Direction.RIGHT, *dirs]
        could_collide_dirs = set()
        will_collide_dirs = set()
        self._ui.wm_title("_")
        if self.boxed_in:
            # follow wall(s)
            self._ui.wm_title("boxed in!")
            relative_left = self._current_dir.rotate_ccw()
            if not self._will_collide(relative_left):
                max_dir = relative_left
            elif not self._will_collide(self._current_dir):
                max_dir = self._current_dir
            else:
                max_dir = self._current_dir.rotate_cw()
            move_reason = MoveReason.BOXED
        elif not self.should_do_floodfill() and not self._will_collide(self._current_dir) and not self._is_player_near(self._current_dir.get_x(pos_x, self._game_width), self._current_dir.get_y(pos_y, self._game_height)):
            max_dir = self._current_dir
            move_reason = MoveReason.CONTINUE
        else:
            for direc in dirs:
                if self._will_collide(direc):
                    will_collide_dirs.add(direc)
                    print(f"Not moving {direc} beacuse i would collide with myself!")
                    continue
                new_x = direc.get_x(pos_x, self._game_width)
                new_y = direc.get_y(pos_y, self._game_height)
                amount, amount_players = FieldCountAlgo.flood_fill_count(self._grid, new_x, new_y, self._game_width,
                                                                         self._game_height, self._last_positions)
                print("%s has %i neighbors with %i players" % (direc.name, amount, amount_players))
                could_collide = self._is_player_near(new_x, new_y)
                if could_collide:
                    could_collide_dirs.add(direc)
                    #print("Not moving to %s because we could collide with another player!" % direc.name)
                    continue
                if amount > max_fields:
                    max_dir = direc
                    move_reason = MoveReason.FLOOD_FILL
                    max_fields = amount / (1 + amount_players)
                    max_players = amount_players
                if max_fields >= 1000:
                    break
            if max_players == 1:  # myself
                message = "I'm trapped!"
                self.boxed_in = True
            if max_fields <= 20:
                message = "shit..."
        if message is None and self._tick - self._last_message_tick >= 100:
            message = random.choice(open("random_messages.txt").readlines())
            self._last_message_tick = self._tick
        if len(could_collide_dirs) + len(will_collide_dirs) == 4:
            print("All options are bad")
            message = "This is close!"
            if len(could_collide_dirs) == 0:
                message = "see ya!"
            else:
                move_reason = MoveReason.RANDOM
                max_dir = random.choice(list(could_collide_dirs))
        print("decided to move %s" % max_dir.name)
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        self._move_reasons[max_dir.get_x(pos_x, self._game_width)][max_dir.get_y(pos_y, self._game_height)] = move_reason.value
        self._current_dir = max_dir
        self._ui.update_game(self._last_positions, self._grid, self._own_playerid, could_collide_dirs, max_dir, self._move_reasons)
        return max_dir, message

        # if chosen is not None:
        #    self._current_dir = chosen
        # return chosen

    def _get_field_at(self, x: int, y: int, dir: Direction) -> int:
        if dir == Direction.LEFT:
            return self._grid[(x - 1) % self._game_width][y]
        elif dir == Direction.RIGHT:
            return self._grid[(x + 1) % self._game_width][y]
        elif dir == Direction.UP:
            return self._grid[x][(y - 1) % self._game_height]
        elif dir == Direction.DOWN:
            return self._grid[x][(y + 1) % self._game_height]

    def remove_player(self, player_id: int):
        self._last_positions.pop(player_id)
        for row in range(self._game_height):
            for col in range(self._game_width):
                if self._grid[row][col] == player_id:
                    self._grid[row][col] = None

    def __repr__(self):
        data = ""
        for row in range(self._game_width):
            row_str = ""
            for col in range(self._game_height):
                field = self._grid[col][row]
                rep = " "
                if field == self._own_playerid:
                    rep = "*"
                elif field is not None:
                    rep = "#"
                row_str += rep + " "
            data += row_str + "\n"
        return data

    def remove_self(self):
        self.remove_player(self._own_playerid)
