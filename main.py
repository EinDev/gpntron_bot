import asyncio
import socket
import sys
import threading
from concurrent.futures import thread


class GameState:
    def __init__(self, width: int, height: int, own_playerid: int):
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(own_playerid, int)
        self._own_playerid = own_playerid
        self._game_width = width
        self._game_height = height
        self._grid = [[None] * height for _ in range(width)]
        self._current_dir = "up"
        self._last_positions = {}

    def update_player_pos(self, playerid: int, pos_x: int, pos_y: int):
        # assert self._grid[pos_x][pos_y] is None
        self._grid[pos_x][pos_y] = playerid
        self._last_positions[playerid] = [pos_y, pos_y]

    def _will_collide(self, dir: str):
        pos_x = self._last_positions[self._own_playerid][0]
        pos_y = self._last_positions[self._own_playerid][1]
        if dir == "up":
            return self._grid[pos_x][pos_y+1] is not None
        return False

    def get_move(self) -> str:
        if self._will_collide(self._current_dir):
            return "left"
        return None

    def remove_player(self, player_id: int):
        for row in range(self._game_height):
            for col in range(self._game_width):
                if self._grid[row][col] == player_id:
                    self._grid[row][col] = None

    def __repr__(self):
        data = ""
        for row in range(self._game_width):
            row_str = ""
            for col in range(self._game_height):
                field = self._grid[row][col]
                rep = " "
                if field == self._own_playerid:
                    rep = "*"
                elif field is not None:
                    rep = "#"
                row_str += rep + " "
            data += row_str + "\n"
        return data


class ConnectionContext:
    def __init__(self, dns, port):
        #ip = socket.getaddrinfo(dns, None, socket.AF_INET6)[0][4][0]
        #print("Resolved IP: %s" % str(ip))
        self._sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self._sock.connect((dns, port))
        print("Connected!")
        self._connected = True
        self._username = open('username.txt').readline()
        self._password = open('password.txt').readline()
        self._loop = asyncio.get_event_loop()
        self._state = None

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
            for player_id in args:
                self._state.remove_player(int(player_id))
        elif code == "tick":
            if self._state is not None:
                print("Tick:")
                print(self._state)
                move_dir = self._state.get_move()
                if move_dir is not None:
                    await self._send("move", [move_dir])
        elif code == "game":
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


async def connect(dns, port):
    print("Connecting to %s:%i" % (dns, port))
    loop = asyncio.get_event_loop()
    ctx = ConnectionContext(dns, port)
    loop.create_task(ctx.client_loop())


if __name__ == '__main__':
    #asyncio.run(connect('gpn-tron.duckdns.org', 4000))
    asyncio.run(connect('2001:67c:20a1:232:a85a:a238:a032:df71', 4000))
