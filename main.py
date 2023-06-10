import asyncio
import queue
import random
import socket
import sys
from enum import Enum
from typing import Optional

random_messages = ["Running on python", "...", "powered by mate", "meow", "The cake is a lie", "speed 2X"]


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

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

    def get_move(self, tick: int) -> Optional[tuple[Direction, str]]:
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        max_fields = 0
        max_dir = Direction.UP
        max_players = 0
        message = None
        dirs = [d for d in Direction]
        if not self.boxed_in:
            random.shuffle(dirs)
        for direc in dirs:
            new_x = direc.get_x(pos_x, self._game_width)
            new_y = direc.get_y(pos_y, self._game_height)
            amount, amount_players = FieldCountAlgo.flood_fill_count(self._grid, new_x, new_y, self._game_width,
                                                                     self._game_height, self._last_positions)
            print("%s has %i neighbors with %i players" % (direc.name, amount, amount_players))
            could_collide = self._is_player_near(new_x, new_y)
            if could_collide:
                print("Not moving to %s because we could collide with another player!" % direc.name)
                continue
            if amount > max_fields:
                max_dir = direc
                max_fields = amount
                max_players = amount_players
            if max_fields >= 1000:
                break
        if max_players == 1:  # myself
            message = "I'm trapped!"
            self.boxed_in = True
        if max_fields <= 20:
            message = "shit..."
        if message is None and tick - self._last_message_tick >= 100:
            message = random.choice(open("random_messages.txt").readlines())
            self._last_message_tick = tick
        print("decided to move %s" % max_dir.name)
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


class ConnectionContext:
    def __init__(self, dns, port):
        # ip = socket.getaddrinfo(dns, None, socket.AF_INET6)[0][4][0]
        # print("Resolved IP: %s" % str(ip))
        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self._sock.connect((dns, port))
        print("Connected!")
        self._connected = True
        self._username = open('username.txt').readline()
        self._password = open('password.txt').readline()
        self._loop = asyncio.get_event_loop()
        self._state = None
        self._tick = 0

    async def client_loop(self):
        while self._connected:
            data = await self._loop.sock_recv(self._sock, 1024)
            if not data:
                self._connected = False
                return
            # print("Got msg: %s" % data.decode('utf8'))
            msgs = data.decode('utf8').split("\n")
            for msg in msgs[:-1]:
                await self.handle_msg(msg)

    async def handle_msg(self, msg):
        code = msg.split('|')[0]
        args = msg.split('|')[1:]
        if code == "motd":
            print("MOTD: %s" % args[0])
            await self._join()
        elif code == "error":
            print("ERROR FROM UPSTREAM: %s" % (str(args)), file=sys.stderr)
        elif code == "message":
            pass  # Wtf we want to ignore messages
        elif code == "die":
            self._state.boxed_in = False
            for player_id in args:
                print("Removing player %i" % int(player_id))
                self._state.remove_player(int(player_id))
        elif code == "lose":
            self._state.remove_self()
            print("LOST", file=sys.stderr)
        elif code == "tick":
            if self._state is not None:
                self._tick += 1
                move_dir, message = self._state.get_move(self._tick)
                if message is not None:
                    await self._send("chat", [message])
                if move_dir is not None:
                    print("moving to %s" % move_dir.name)
                    await self._send("move", [move_dir.value])
        elif code == "game":
            self._tick = 0
            width = int(args[0])
            height = int(args[1])
            own_player_id = int(args[2])
            self._state = GameState(width, height, own_player_id)
            print("Got game state!")
        elif code == "pos":
            player_id = int(args[0])
            x = int(args[1])
            y = int(args[2])
            self._state.update_player_pos(player_id, x, y)
        else:
            print("Unknown code %s: %s" % (code, str(args)))

    async def chat(self, message: str):
        await self._send("chat", [message])

    async def _send(self, code: str, data: list[str]):
        assert isinstance(code, str)
        assert isinstance(data, list)
        msg = [code]
        msg.extend(data)
        msg = "|".join(msg) + "\n"
        print("sending '%s'..." % code)
        await self._loop.sock_sendall(self._sock, msg.encode('utf8'))

    async def _join(self):
        await self._send("join", [self._username, self._password])


async def manual_event_server(ctx: ConnectionContext):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind(("127.0.0.1", 4006))
    loop = asyncio.get_event_loop()
    print("Starting BME")
    while True:
        try:
            data = (await loop.sock_recv(sock, 1024)).decode('utf8').rstrip("\n")
            print(data)
            code = data.split('|')[0]
            args = data.split('|')[:-1]
            if code == "msg":
                await ctx.chat(args[0])
        except:
            pass


async def connect(dns, port):
    print("Connecting to %s:%i" % (dns, port))
    loop = asyncio.get_event_loop()
    ctx = ConnectionContext(dns, port)
    loop.create_task(ctx.client_loop())


if __name__ == '__main__':
    asyncio.run(connect('gpn-tron.duckdns.org', 4000))
    # asyncio.run(connect('2001:67c:20a1:232:d681:d7ff:fe8c:5033', 4000))
