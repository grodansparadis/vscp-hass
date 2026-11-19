"""Minimal asynchronous VSCP TCP/IP link client.

Uses one command connection and one dedicated RCVLOOP connection.
"""
import asyncio
from dataclasses import dataclass

class VSCPError(Exception):
    """Link error."""

@dataclass(frozen=True)
class Event:
    head: int
    vscp_class: int
    vscp_type: int
    obid: int
    timestamp: int
    guid: str
    data: tuple[int, ...]

    @classmethod
    def parse(cls, line: str):
        fields = line.strip().split(",")
        if len(fields) < 6:
            raise ValueError("short VSCP event")
        head, vc, vt, obid, timestamp = (int(x) for x in fields[:5])
        guid = fields[5].lower()
        if len(guid.split(":")) != 16 or any(len(x) != 2 or int(x, 16) > 255 for x in guid.split(":")):
            raise ValueError("invalid GUID")
        data = tuple(int(x) for x in fields[6:] if x != "")
        if any(not 0 <= x <= 255 for x in data):
            raise ValueError("invalid data byte")
        return cls(head, vc, vt, obid, timestamp, guid, data)

    def wire(self):
        return ",".join(map(str, (self.head, self.vscp_class, self.vscp_type,
                                    self.obid, self.timestamp))) + "," + self.guid + (
            "," + ",".join(map(str, self.data)) if self.data else "")

class Link:
    def __init__(self, host, port, username, password):
        self.host, self.port = host, port
        self.username, self.password = username, password
        self.reader = self.writer = None
        self.lock = asyncio.Lock()

    async def _line(self):
        raw = await asyncio.wait_for(self.reader.readline(), 10)
        if not raw:
            raise VSCPError("connection closed")
        return raw.decode('utf-8', 'replace').strip()

    async def _ok(self):
        line = await self._line()
        if not line.startswith('+OK'):
            raise VSCPError(line)
        return line

    async def connect(self):
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), 10)
        await self._ok()  # greeting
        await self.command('USER ' + self.username)
        await self.command('PASS ' + self.password)

    async def command(self, command):
        async with self.lock:
            if self.writer is None:
                raise VSCPError('not connected')
            self.writer.write((command + '\r\n').encode())
            await self.writer.drain()
            return await self._ok()

    async def send(self, event):
        return await self.command('SEND ' + event.wire())

    async def receive_loop(self, callback):
        await self.command('RCVLOOP')
        while True:
            line = await self._line()
            if line.startswith('+OK'):
                continue
            if line.startswith('-ERR'):
                raise VSCPError(line)
            try:
                event = Event.parse(line)
            except (ValueError, OverflowError):
                continue
            await callback(event)

    async def close(self):
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except OSError:
                pass
        self.reader = self.writer = None
