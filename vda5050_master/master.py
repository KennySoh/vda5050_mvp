from __future__ import annotations

import logging
import uuid
from enum import Enum
from typing import Callable, List, Tuple

from vda5050_common.models import (
    ActionStatus,
    Connection,
    ConnectionState,
    ErrorLevel,
    Factsheet,
    InstantActions,
    Order,
    State,
)
from vda5050_common.time import next_header_id
from vda5050_common.topics import agv_topic

from vda5050_master.fleet import Agv, Fleet
from vda5050_master.orders import build_instant_actions, build_order

logger = logging.getLogger(__name__)


class AssignmentDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"  # V2 — needs the stitch queue, docs/design_doc.md §9.11
    REJECTED_PREFLIGHT = "REJECTED_PREFLIGHT"
    REJECTED_POSTFLIGHT = "REJECTED_POSTFLIGHT"  # reserved — not emitted yet, same as the reference


class OrderPhase(str, Enum):
    NO_ORDER = "NO_ORDER"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MasterConnectionState(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    SHUTTING_DOWN = "SHUTTING_DOWN"


class Master:
    def __init__(
        self,
        fleet: Fleet,
        publish_order: Callable[[Agv, Order], None],
        publish_instant_actions: Callable[[Agv, InstantActions], None],
    ) -> None:
        self.fleet = fleet
        self.connection_state = MasterConnectionState.STARTING
        self._order_phases: dict[str, OrderPhase] = {}
        self._publish_order = publish_order
        self._publish_instant_actions = publish_instant_actions

    def order_phase(self, agv: Agv) -> OrderPhase:
        return self._order_phases.get(agv.agv_id, OrderPhase.NO_ORDER)

    def on_mqtt_connected(self) -> None:
        self.connection_state = MasterConnectionState.READY
        logger.info("event=master.connection_state state=%s", self.connection_state.value)

    def on_mqtt_disconnected(self) -> None:
        if self.connection_state == MasterConnectionState.SHUTTING_DOWN:
            return
        self.connection_state = MasterConnectionState.DEGRADED
        logger.info("event=master.connection_state state=%s", self.connection_state.value)

    def shutdown(self) -> None:
        self.connection_state = MasterConnectionState.SHUTTING_DOWN
        logger.info("event=master.connection_state state=%s", self.connection_state.value)

    def cancel_order(self, agv: Agv) -> None:
        header_id = next_header_id(
            agv_topic(agv.manufacturer, agv.serial_number, "instantActions")
        )
        instant_actions = build_instant_actions(agv, "cancelOrder", header_id=header_id)
        self._publish_instant_actions(agv, instant_actions)
        logger.info(
            "event=cancel.requested agv_id=%s order_id=%s", agv.agv_id, agv.current_order_id
        )

    def assign_order(
        self, agv_id: str, waypoints: List[Tuple[float, float]]
    ) -> Tuple[str, AssignmentDecision]:
        assignment_id = str(uuid.uuid4())
        agv = self.fleet.get(agv_id)
        if agv is None:
            logger.info(
                "event=order.rejected assignment_id=%s agv_id=%s reason=unknown_agv",
                assignment_id,
                agv_id,
            )
            return assignment_id, AssignmentDecision.REJECTED_PREFLIGHT

        header_id = next_header_id(agv_topic(agv.manufacturer, agv.serial_number, "order"))
        order = build_order(agv, waypoints, header_id=header_id)
        agv.current_order_id = order.orderId
        agv.current_order_update_id = order.orderUpdateId
        self._order_phases[agv.agv_id] = OrderPhase.ACCEPTED
        self._publish_order(agv, order)
        logger.info(
            "event=order.published assignment_id=%s agv_id=%s order_id=%s",
            assignment_id,
            agv_id,
            order.orderId,
        )
        return assignment_id, AssignmentDecision.ACCEPTED

    def on_state(self, agv: Agv, state: State) -> None:
        self.fleet.record_state(agv, state)
        if self._is_order_completed(state):
            self._handle_order_completed(agv, state)
            return
        if state.newBaseRequest:
            self._handle_new_base_request(agv, state)
            return
        if self._has_fatal_error(state):
            self._handle_order_error(agv, state)
            return
        self._record_progress(agv, state)

    def on_connection(self, agv: Agv, connection: Connection) -> None:
        self.fleet.record_connection(agv, connection)
        if connection.connectionState == ConnectionState.CONNECTIONBROKEN:
            self.fleet.mark_unreachable(agv)

    def on_factsheet(self, agv: Agv, factsheet: Factsheet) -> None:
        self.fleet.record_factsheet(agv, factsheet)

    def _is_order_completed(self, state: State) -> bool:
        return (
            bool(state.orderId)
            and not state.nodeStates
            and not state.edgeStates
            and all(
                action.actionStatus in (ActionStatus.FINISHED, ActionStatus.FAILED)
                for action in state.actionStates
            )
        )

    def _handle_order_completed(self, agv: Agv, state: State) -> None:
        already_handled = (
            self._order_phases.get(agv.agv_id) == OrderPhase.COMPLETED and not agv.current_order_id
        )
        if already_handled:
            return
        self._order_phases[agv.agv_id] = OrderPhase.COMPLETED
        self.fleet.clear_current_order(agv)
        logger.info("event=order.completed agv_id=%s order_id=%s", agv.agv_id, state.orderId)

    def _handle_new_base_request(self, agv: Agv, state: State) -> None:
        logger.info(
            "event=new_base_request.received agv_id=%s (not implemented yet, V1/V2)", agv.agv_id
        )

    def _has_fatal_error(self, state: State) -> bool:
        return any(error.errorLevel == ErrorLevel.FATAL for error in state.errors)

    def _handle_order_error(self, agv: Agv, state: State) -> None:
        self._order_phases[agv.agv_id] = OrderPhase.FAILED
        logger.info("event=order.failed agv_id=%s order_id=%s", agv.agv_id, state.orderId)

    def _record_progress(self, agv: Agv, state: State) -> None:
        self._order_phases[agv.agv_id] = OrderPhase.RUNNING
        logger.info(
            "event=order.progress agv_id=%s order_id=%s remaining_nodes=%d",
            agv.agv_id,
            state.orderId,
            len(state.nodeStates),
        )
