import asyncio
import pytest
from custom_components.vscp.protocol import Event, Link, VSCPError
GUID = ':'.join(['00']*15+['01'])

def test_event_roundtrip():
    e = Event(0, 10, 6, 0, 0, GUID, (1, 2, 255))
    assert Event.parse(e.wire()) == e

@pytest.mark.parametrize('raw', ['1,2', '0,1,2,0,0,bad,1', f'0,1,2,0,0,{GUID},256'])
def test_bad_event(raw):
    with pytest.raises(ValueError):
        Event.parse(raw)

@pytest.mark.asyncio
async def test_link_login_send_and_receive():
    commands = []
    async def server(reader, writer):
        writer.write(b'+OK VSCP daemon\r\n'); await writer.drain()
        while line := await reader.readline():
            cmd = line.decode().strip(); commands.append(cmd)
            writer.write(b'+OK\r\n')
            if cmd == 'RCVLOOP':
                writer.write(f'0,10,6,0,0,{GUID},1,2\r\n'.encode())
            await writer.drain()
        writer.close()
    srv = await asyncio.start_server(server, '127.0.0.1', 0)
    port = srv.sockets[0].getsockname()[1]
    try:
        link = Link('127.0.0.1', port, 'test', 'secret')
        await link.connect()
        await link.send(Event(0, 10, 6, 0, 0, GUID, (3,)))
        events = []
        async def callback(e):
            events.append(e)
            raise asyncio.CancelledError
        with pytest.raises(asyncio.CancelledError):
            await link.receive_loop(callback)
        assert events[0].data == (1, 2)
        assert commands[:2] == ['USER test', 'PASS secret']
        assert any(x.startswith('SEND ') for x in commands)
        await link.close()
    finally:
        srv.close(); await srv.wait_closed()
