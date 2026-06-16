from __future__ import annotations

import logging
from typing import List, Tuple

from vda5050_common.models import Connection, Factsheet, State

from vda5050_master.fleet import Fleet
from vda5050_master.master import AssignmentDecision, Master, OrderPhase
from vda5050_master.mqtt import MasterMqtt

logger = logging.getLogger(__name__)


class MasterApp:
    def __init__(self, host: str = "127.0.0.1", port: int = 1883) -> None:
        self.fleet = Fleet()
        self.mqtt = MasterMqtt(host=host, port=port)
        self.master = Master(
            self.fleet,
            publish_order=self.mqtt.publish_order,
            publish_instant_actions=self.mqtt.publish_instant_actions,
        )
        self.mqtt.on_connected(self.master.on_mqtt_connected)
        self.mqtt.on_disconnected(self.master.on_mqtt_disconnected)
        self.mqtt.on_state(self._handle_state)
        self.mqtt.on_connection(self._handle_connection)
        self.mqtt.on_factsheet(self._handle_factsheet)

    def start(self) -> None:
        self.mqtt.connect()

    def stop(self) -> None:
        self.master.shutdown()
        self.mqtt.disconnect()

    def assign_order(
        self, agv_id: str, waypoints: List[Tuple[float, float]]
    ) -> Tuple[str, AssignmentDecision]:
        return self.master.assign_order(agv_id, waypoints)

    def cancel_order(self, agv_id: str) -> bool:
        agv = self.fleet.get(agv_id)
        if agv is None:
            return False
        self.master.cancel_order(agv)
        return True

    def order_phase(self, agv_id: str) -> OrderPhase:
        agv = self.fleet.get(agv_id)
        if agv is None:
            return OrderPhase.NO_ORDER
        return self.master.order_phase(agv)

    def _handle_state(self, state: State) -> None:
        agv = self.fleet.get_or_create(state.manufacturer, state.serialNumber)
        self.master.on_state(agv, state)

    def _handle_connection(self, connection: Connection) -> None:
        agv = self.fleet.get_or_create(connection.manufacturer, connection.serialNumber)
        self.master.on_connection(agv, connection)

    def _handle_factsheet(self, factsheet: Factsheet) -> None:
        agv = self.fleet.get_or_create(factsheet.manufacturer, factsheet.serialNumber)
        self.master.on_factsheet(agv, factsheet)


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    app = MasterApp()
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
