from __future__ import annotations

import logging
import time
from typing import List

from vda5050_common.models import (
    BatteryState,
    EStop,
    Error,
    OperatingMode,
    SafetyState,
    State,
)
from vda5050_common.time import next_header_id, now_iso8601
from vda5050_common.topics import PROTOCOL_VERSION

from vda5050_client.actions import ActionRunner
from vda5050_client.orders import ClientOrderState
from vda5050_client.vehicle import Vehicle

logger = logging.getLogger(__name__)


class StateBuilder:
    def __init__(
        self,
        manufacturer: str,
        serial_number: str,
        topic_name: str,
        heartbeat_seconds: float = 1.0,
    ) -> None:
        self._manufacturer = manufacturer
        self._serial_number = serial_number
        self._topic_name = topic_name
        self._dirty = False
        self._errors: List[Error] = []
        self._heartbeat_seconds = heartbeat_seconds
        self._last_published_at = time.monotonic()

    def mark_dirty(self, reason: str) -> None:
        logger.info("event=state.dirty reason=%s", reason)
        self._dirty = True

    def should_publish(self) -> bool:
        if self._dirty:
            return True
        return (time.monotonic() - self._last_published_at) >= self._heartbeat_seconds

    def clear_dirty(self) -> None:
        self._dirty = False
        self._last_published_at = time.monotonic()

    def add_error(self, error: Error) -> None:
        self._errors.append(error)
        self.mark_dirty("error_added")

    def build_state(
        self,
        orders: ClientOrderState,
        vehicle: Vehicle,
        actions: ActionRunner,
    ) -> State:
        return State(
            headerId=next_header_id(self._topic_name),
            timestamp=now_iso8601(),
            version=PROTOCOL_VERSION,
            manufacturer=self._manufacturer,
            serialNumber=self._serial_number,
            orderId=orders.order_id,
            orderUpdateId=orders.order_update_id,
            lastNodeId=orders.last_node_id,
            lastNodeSequenceId=orders.last_node_sequence_id,
            nodeStates=orders.node_states(),
            edgeStates=orders.edge_states(),
            driving=vehicle.driving,
            actionStates=actions.action_states(),
            batteryState=BatteryState(batteryCharge=100.0, charging=False),
            operatingMode=OperatingMode.AUTOMATIC,
            errors=list(self._errors),
            safetyState=SafetyState(eStop=EStop.NONE, fieldViolation=False),
        )
