from __future__ import annotations

import math
from typing import List, Optional, Tuple

from vda5050_common.models import (
    ActionState,
    ActionStatus,
    Edge,
    EdgeState,
    Error,
    ErrorLevel,
    ErrorReference,
    Node,
    NodeState,
    Order,
)


class ClientOrderState:
    def __init__(self) -> None:
        self.order_id: str = ""
        self.order_update_id: int = 0
        self.last_node_id: str = ""
        self.last_node_sequence_id: int = 0
        self._nodes: List[Node] = []
        self._edges: List[Edge] = []
        self._remaining_node_ids: List[str] = []
        self._remaining_edge_ids: List[str] = []
        self._active = False
        self._completion_reported = False

    def has_active_order(self) -> bool:
        return self._active

    def accept_or_reject(
        self, order: Order, current_position: Optional[Tuple[float, float]] = None
    ) -> Optional[Error]:
        if not order.nodes:
            return self._error(order, "validationError", "order has no nodes")

        sequence_problem = self._validate_sequence(order)
        if sequence_problem is not None:
            return self._error(order, "validationError", sequence_problem)

        if order.orderId == self.order_id:
            if order.orderUpdateId <= self.order_update_id:
                return self._error(
                    order,
                    "orderUpdateError",
                    "orderUpdateId is not newer than the current order",
                )
        elif self.has_active_order():
            return self._error(order, "orderError", "AGV already executing another order")
        else:
            first_node = order.nodes[0]
            if not self._is_first_node_reachable(first_node, current_position):
                return self._error(
                    order,
                    "orderError",
                    f"first node {first_node.nodeId} is not reachable from current position",
                )

        return None

    def _validate_sequence(self, order: Order) -> Optional[str]:
        if len(order.edges) != len(order.nodes) - 1:
            return "edge count does not match node count - 1"
        for i, edge in enumerate(order.edges):
            if edge.startNodeId != order.nodes[i].nodeId or edge.endNodeId != order.nodes[i + 1].nodeId:
                return f"edge {edge.edgeId} does not connect nodes {i} and {i + 1} in sequence"
        seen_unreleased = False
        for node in order.nodes:
            if seen_unreleased and node.released:
                return f"released node {node.nodeId} follows an unreleased node"
            if not node.released:
                seen_unreleased = True
        return None

    def _is_first_node_reachable(
        self, node: Node, current_position: Optional[Tuple[float, float]]
    ) -> bool:
        if current_position is None or node.nodePosition is None:
            return True
        deviation = max(node.nodePosition.allowedDeviationXY or 0.0, 0.01)
        distance = math.hypot(
            node.nodePosition.x - current_position[0], node.nodePosition.y - current_position[1]
        )
        return distance <= deviation

    def _error(self, order: Order, error_type: str, description: str) -> Error:
        return Error(
            errorType=error_type,
            errorLevel=ErrorLevel.WARNING,
            errorDescription=description,
            errorReferences=[ErrorReference(referenceKey="orderId", referenceValue=order.orderId)],
        )

    def apply_order(self, order: Order) -> None:
        self.order_id = order.orderId
        self.order_update_id = order.orderUpdateId
        self._nodes = order.nodes
        self._edges = order.edges
        self._remaining_node_ids = [node.nodeId for node in order.nodes]
        self._remaining_edge_ids = [edge.edgeId for edge in order.edges]
        self._active = True
        self._completion_reported = False

    def cancel_order(self) -> None:
        self._remaining_node_ids = []
        self._remaining_edge_ids = []

    def next_node(self) -> Optional[Node]:
        for node in self._nodes:
            if node.nodeId in self._remaining_node_ids:
                return node
        return None

    def mark_node_reached(self, node_id: str) -> None:
        node = next((n for n in self._nodes if n.nodeId == node_id), None)
        if node is None or node_id not in self._remaining_node_ids:
            return
        self._remaining_node_ids.remove(node_id)
        self.last_node_id = node_id
        self.last_node_sequence_id = node.sequenceId
        incoming_edge = next((e for e in self._edges if e.endNodeId == node_id), None)
        if incoming_edge is not None and incoming_edge.edgeId in self._remaining_edge_ids:
            self._remaining_edge_ids.remove(incoming_edge.edgeId)

    def node_states(self) -> List[NodeState]:
        return [
            NodeState(
                nodeId=node.nodeId,
                sequenceId=node.sequenceId,
                released=node.released,
                nodePosition=node.nodePosition,
            )
            for node in self._nodes
            if node.nodeId in self._remaining_node_ids
        ]

    def edge_states(self) -> List[EdgeState]:
        return [
            EdgeState(
                edgeId=edge.edgeId,
                sequenceId=edge.sequenceId,
                released=edge.released,
            )
            for edge in self._edges
            if edge.edgeId in self._remaining_edge_ids
        ]

    def is_order_complete(self, action_states: List[ActionState]) -> bool:
        return (
            not self._remaining_node_ids
            and not self._remaining_edge_ids
            and all(
                action.actionStatus in (ActionStatus.FINISHED, ActionStatus.FAILED)
                for action in action_states
            )
        )

    def check_newly_completed(self, action_states: List[ActionState]) -> bool:
        if self._completion_reported:
            return False
        if self.is_order_complete(action_states):
            self._completion_reported = True
            self._active = False
            return True
        return False
