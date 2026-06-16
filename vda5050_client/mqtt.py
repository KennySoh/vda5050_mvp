from __future__ import annotations

from typing import Callable, Optional

from vda5050_common.models import (
    Connection,
    ConnectionState,
    Factsheet,
    InstantActions,
    Order,
    State,
)
from vda5050_common.mqtt import MqttConnection
from vda5050_common.time import next_header_id, now_iso8601
from vda5050_common.topics import PROTOCOL_VERSION, agv_topic


class ClientMqtt:
    def __init__(
        self,
        manufacturer: str,
        serial_number: str,
        host: str = "127.0.0.1",
        port: int = 1883,
    ) -> None:
        self.manufacturer = manufacturer
        self.serial_number = serial_number
        self._order_topic = agv_topic(manufacturer, serial_number, "order")
        self._instant_actions_topic = agv_topic(manufacturer, serial_number, "instantActions")
        self._state_topic = agv_topic(manufacturer, serial_number, "state")
        self._connection_topic = agv_topic(manufacturer, serial_number, "connection")
        self._factsheet_topic = agv_topic(manufacturer, serial_number, "factsheet")
        self._conn = MqttConnection(
            client_id=f"client-{manufacturer}-{serial_number}", host=host, port=port
        )
        self._on_order: Optional[Callable[[Order], None]] = None
        self._on_instant_actions: Optional[Callable[[InstantActions], None]] = None

    def on_order(self, callback: Callable[[Order], None]) -> None:
        self._on_order = callback

    def on_instant_actions(self, callback: Callable[[InstantActions], None]) -> None:
        self._on_instant_actions = callback

    def connect(self, factsheet: Factsheet) -> None:
        last_will = Connection(
            headerId=0,
            timestamp=now_iso8601(),
            version=PROTOCOL_VERSION,
            manufacturer=self.manufacturer,
            serialNumber=self.serial_number,
            connectionState=ConnectionState.CONNECTIONBROKEN,
        )
        self._conn.set_last_will(self._connection_topic, last_will, retain=True)
        self._conn.subscribe(self._order_topic, self._handle_order)
        self._conn.subscribe(self._instant_actions_topic, self._handle_instant_actions)
        self._conn.connect()
        self.publish_connection(ConnectionState.ONLINE)
        self._conn.publish(self._factsheet_topic, factsheet, retain=True)

    def stop(self) -> None:
        self.publish_connection(ConnectionState.OFFLINE)
        self._conn.disconnect()

    def publish_connection(self, state: ConnectionState) -> None:
        message = Connection(
            headerId=next_header_id(self._connection_topic),
            timestamp=now_iso8601(),
            version=PROTOCOL_VERSION,
            manufacturer=self.manufacturer,
            serialNumber=self.serial_number,
            connectionState=state,
        )
        self._conn.publish(self._connection_topic, message, retain=True)

    def publish_state(self, state: State) -> None:
        self._conn.publish(self._state_topic, state)

    def _handle_order(self, payload: bytes) -> None:
        order = Order.model_validate_json(payload)
        if self._on_order is not None:
            self._on_order(order)

    def _handle_instant_actions(self, payload: bytes) -> None:
        instant_actions = InstantActions.model_validate_json(payload)
        if self._on_instant_actions is not None:
            self._on_instant_actions(instant_actions)
