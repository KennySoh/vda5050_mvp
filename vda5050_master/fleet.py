from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from vda5050_common.models import Connection, ConnectionState, Factsheet, State

logger = logging.getLogger(__name__)


@dataclass
class Agv:
    manufacturer: str
    serial_number: str
    latest_state: Optional[State] = None
    latest_connection: Optional[Connection] = None
    latest_factsheet: Optional[Factsheet] = None
    current_order_id: str = ""
    current_order_update_id: int = 0
    reachable: bool = True

    @property
    def agv_id(self) -> str:
        return f"{self.manufacturer}/{self.serial_number}"


class Fleet:
    def __init__(self) -> None:
        self._agvs: dict[str, Agv] = {}

    def get_or_create(self, manufacturer: str, serial_number: str) -> Agv:
        key = f"{manufacturer}/{serial_number}"
        agv = self._agvs.get(key)
        if agv is None:
            agv = Agv(manufacturer=manufacturer, serial_number=serial_number)
            self._agvs[key] = agv
            logger.info("event=agv.registered agv_id=%s", key)
        return agv

    def get(self, agv_id: str) -> Optional[Agv]:
        return self._agvs.get(agv_id)

    def record_connection(self, agv: Agv, connection: Connection) -> None:
        agv.latest_connection = connection
        if connection.connectionState == ConnectionState.ONLINE:
            agv.reachable = True

    def record_factsheet(self, agv: Agv, factsheet: Factsheet) -> None:
        agv.latest_factsheet = factsheet

    def record_state(self, agv: Agv, state: State) -> None:
        agv.latest_state = state

    def clear_current_order(self, agv: Agv) -> None:
        agv.current_order_id = ""
        agv.current_order_update_id = 0

    def mark_unreachable(self, agv: Agv) -> None:
        agv.reachable = False
        logger.info("event=agv.marked_unreachable agv_id=%s", agv.agv_id)
