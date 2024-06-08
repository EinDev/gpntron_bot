import argparse
import asyncio
import socket
import sys
import time

from click import getchar

from game_state import GameState

random_messages = ["Running on python", "...", "powered by mate", "meow", "The cake is a lie", "speed 2X"]



class ConnectionContext:
    def __init__(self, dns, port):
        # ip = socket.getaddrinfo(dns, None, socket.AF_INET6)[0][4][0]
        # print("Resolved IP: %s" % str(ip))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((dns, port))
        print("Connected!")
        self._connected = True
        self._username = open('username.txt').read().splitlines()[0]
        self._password = open('password.txt').read().splitlines()[0]
        self._loop = asyncio.get_event_loop()
        self._state = None
        self._tick = 0

    async def client_loop(self):
        msg_buf = ""
        while self._connected:
            data = await self._loop.sock_recv(self._sock, 1024)
            if not data:
                self._connected = False
                return
            # print("Got msg: %s" % data.decode('utf8'))
            msgs = (msg_buf + data.decode('utf8')).split("\n")
            msg_buf = ""
            if len(msgs[-1]) != 0:
                msg_buf = msgs[-1]
            for msg in msgs[:-1]:
                await self.handle_msg(msg)

    async def handle_msg(self, msg):
        #print(f"< {msg}")
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
            #time.sleep(10000)
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
        #print(f"> {msg}")
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
    parser = argparse.ArgumentParser(
        prog='ProgramName',
        description='What the program does',
        epilog='Text at the bottom of help')
    parser.add_argument('server')  # positional argument
    parser.add_argument('-p', '--port', default=4000)
    args = parser.parse_args()
    asyncio.run(connect(args.server, args.port))

    # asyncio.run(connect('2001:67c:20a1:232:d681:d7ff:fe8c:5033', 4000))
