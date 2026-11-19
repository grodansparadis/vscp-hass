"""Connection management and event distribution."""
import asyncio
import logging
from .protocol import Link, Event, VSCPError

_LOGGER = logging.getLogger(__name__)

class Hub:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.tx = self.rx = None
        self.task = None
        self.connected = False
        self.listeners = []
        self.states = {}
        self.stopping = False

    def link(self):
        d = self.entry.data
        return Link(d['host'], d['port'], d['username'], d['password'])

    async def start(self):
        self.tx = self.link()
        await self.tx.connect()
        self.connected = True
        self.task = self.hass.async_create_task(self._run(), eager_start=False)

    async def _run(self):
        while not self.stopping:
            try:
                self.rx = self.link()
                await self.rx.connect()
                await self.rx.receive_loop(self._event)
            except (OSError, asyncio.TimeoutError, VSCPError) as err:
                _LOGGER.warning('VSCP receiver disconnected: %s', err)
            finally:
                if self.rx:
                    await self.rx.close()
                self.rx = None
            if not self.stopping:
                await asyncio.sleep(5)

    async def _event(self, event):
        self.hass.bus.async_fire('vscp_event', {
            'guid': event.guid, 'class': event.vscp_class,
            'type': event.vscp_type, 'data': list(event.data),
            'head': event.head, 'obid': event.obid,
            'timestamp': event.timestamp})
        for listener in tuple(self.listeners):
            listener(event)

    async def send(self, event):
        try:
            await self.tx.send(event)
        except (OSError, asyncio.TimeoutError, VSCPError):
            self.connected = False
            if self.tx:
                await self.tx.close()
            self.tx = self.link()
            await self.tx.connect()
            self.connected = True
            # Never automatically repeat a command whose delivery is uncertain.
            raise VSCPError('connection recovered; command not retried')

    async def stop(self):
        self.stopping = True
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        for link in (self.rx, self.tx):
            if link:
                await link.close()
        self.connected = False
