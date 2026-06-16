from __future__ import annotations

from typing import Callable

from vda5050_common.models import Connection, Factsheet, InstantActions, Order, State
from vda5050_common.mqtt import MqttConnection
from vda5050_common.topics import agv_topic

from vda5050_master.fleet import Agv


class MasterMqtt:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1883,
        client_id: str = "vda5050-master",
    ) -> None:
        self._conn = MqttConnection(client_id=client_id, host=host, port=port)

    def on_connected(self, callback: Callable[[], None]) -> None:
        self._conn.on_connected(callback)

    def on_disconnected(self, callback: Callable[[], None]) -> None:
        self._conn.on_disconnected(callback)

    def on_state(self, callback: Callable[[State], None]) -> None:
        self._conn.subscribe(
            agv_topic("+", "+", "state"),
            lambda payload: callback(State.model_validate_json(payload)),
        )

    def on_connection(self, callback: Callable[[Connection], None]) -> None:
        self._conn.subscribe(
            agv_topic("+", "+", "connection"),
            lambda payload: callback(Connection.model_validate_json(payload)),
        )

    def on_factsheet(self, callback: Callable[[Factsheet], None]) -> None:
        self._conn.subscribe(
            agv_topic("+", "+", "factsheet"),
            lambda payload: callback(Factsheet.model_validate_json(payload)),
        )

    def connect(self) -> None:
        self._conn.connect()

    def disconnect(self) -> None:
        self._conn.disconnect()

    def publish_order(self, agv: Agv, order: Order) -> None:
        self._conn.publish(agv_topic(agv.manufacturer, agv.serial_number, "order"), order)

    def publish_instant_actions(self, agv: Agv, actions: InstantActions) -> None:
        self._conn.publish(
            agv_topic(agv.manufacturer, agv.serial_number, "instantActions"), actions
        )
