from __future__ import annotations

INTERFACE = "uagv"
MAJOR_VERSION = "v2"
PROTOCOL_VERSION = "2.1.0"

QOS = {
    "order": 0,
    "instantActions": 0,
    "state": 0,
    "connection": 1,
    "factsheet": 0,
    "visualization": 0,
}


def topic(
    interface: str,
    major_version: str,
    manufacturer: str,
    serial_number: str,
    name: str,
) -> str:
    return f"{interface}/{major_version}/{manufacturer}/{serial_number}/{name}"


def agv_topic(manufacturer: str, serial_number: str, name: str) -> str:
    return topic(INTERFACE, MAJOR_VERSION, manufacturer, serial_number, name)
