from __future__ import annotations

import math
from dataclasses import dataclass

from vda5050_common.models import Node

from vda5050_client.actions import ActionRunner
from vda5050_client.orders import ClientOrderState


@dataclass
class VehiclePose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class Vehicle:
    def __init__(
        self,
        orders: ClientOrderState,
        actions: ActionRunner,
        speed: float = 0.5,
    ) -> None:
        self.pose = VehiclePose()
        self.driving = False
        self._orders = orders
        self._actions = actions
        self._speed = speed

    def tick(self, dt: float) -> bool:
        if self._actions.is_driving_blocked():
            self.driving = False
            return False

        target_node = self._orders.next_node()
        if target_node is None:
            self.driving = False
            return False

        self.move_towards_next_node(target_node, dt)

        if self.check_node_reached(target_node):
            self.driving = False
            self._orders.mark_node_reached(target_node.nodeId)
            for action in target_node.actions:
                self._actions.start_action(action)
            return True

        return False

    def move_towards_next_node(self, node: Node, dt: float) -> None:
        position = node.nodePosition
        dx = position.x - self.pose.x
        dy = position.y - self.pose.y
        distance = math.hypot(dx, dy)
        if distance < 1e-9:
            self.driving = False
            return
        step = min(self._speed * dt, distance)
        self.pose.x += dx / distance * step
        self.pose.y += dy / distance * step
        self.pose.theta = math.atan2(dy, dx)
        self.driving = True

    def check_node_reached(self, node: Node) -> bool:
        position = node.nodePosition
        deviation = position.allowedDeviationXY or 0.1
        return math.hypot(position.x - self.pose.x, position.y - self.pose.y) <= deviation
