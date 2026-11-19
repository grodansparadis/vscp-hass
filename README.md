# VSCP native TCP/IP integration for Home Assistant (prototype 0.1.0)

## Status

Development prototype, **not hardware validated**. The VSCP TCP/IP link protocol uses line-oriented `USER`, `PASS`, `SEND` and `RCVLOOP` commands. This implementation has a separate transmit and receive connection. Commands are **not** replayed after an ambiguous send failure. This prototype does not implement TLS, MDF discovery, automatic entity discovery, or a full VSCP measurement decoder.

VSCP HASS prototype is in the **vscp_hass_prototype** folder

## Install

1. Copy `custom_components/vscp` into `<Home Assistant config>/custom_components/vscp`.
2. Copy `vscp_entities.example.json` to `<Home Assistant config>/vscp_entities.json` and edit GUIDs, event classes/types, data, offsets and scaling for **your actual firmware**. The sample command payloads are placeholders and must not be sent to hardware without validation.
3. Restart Home Assistant.
4. Settings → Devices & services → Add integration → VSCP TCP/IP. Enter the daemon host, TCP port (default 9598), username and password.
5. Verify the entities appear, then inspect incoming events in Developer Tools → Events, listening to `vscp_event`.

## Mapping schema

Switches: `id`, `name`, `guid`, `command_on`, `command_off`, `state_on`, `state_off`. Each command is a VSCP event with `class`, `type`, optional `head`, `guid`, and `data` (byte array). State match specs use `class`, `type` and optional `data_prefix`. An actual state report is required; a successful SEND response does not mean the relay switched.

Sensors: `id`, `name`, `guid`, `event` match spec, `encoding` (`uint8`, `int16be`, `float32be`), `offset`, optional `scale`, `add`, and `unit`. The example is **not** a generic decoder for VSCP class 10 measurement coding. For real class 10 events, implement the VSCP data-coding format or explicitly map a known fixed payload layout.

The mapping file is read at startup. Restart HA to reload it. Credentials are stored in the HA config entry. Restrict daemon account permissions and network exposure; the connection is plaintext TCP. Prefer an isolated LAN or authenticated VPN.

## Tests

Install `pytest` and `pytest-asyncio` in a test environment, then run `pytest -q`. The protocol test uses a local simulated TCP server. Home Assistant entity/config-flow integration tests and hardware tests remain to be added.

## Existing VSCP4HASS review

`https://github.com/mzanders/vscp4hass` is an earlier VSCP TCP integration. It contains `node.py` and `light.py`; its `manifest.json` has `config_flow: false`. This prototype uses an explicit config flow and independent async transport rather than copying its existing node model. A full line-by-line compatibility audit, especially its register abstractions and channel handling, remains outstanding.

## Known limitations

- RCVLOOP session reconnects, but send availability is not continuously probed.
- No automatic state refresh after reconnect; states may be stale until the next event.
- Sensor payload decoding is a deliberately limited fixed-layout mapping.
- No per-device MDF parsing, register read/write, command correlation, or automatic discovery.
- Only TCP plaintext is implemented; secure tunneling is required on untrusted networks.
- Mapping JSON is not schema-validated; incorrect definitions may fail entity setup.
- `vscp_event` exposes all received event data; avoid transmitting secrets in VSCP events.

## References

- https://docs.vscp.org/
- https://github.com/mzanders/vscp4hass
- https://contributors.home-assistant.io/core/integrations/config-flow/
