from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from vda5050_common.models import (
    Action,
    ActionParameter,
    BlockingType,
    Edge,
    InstantActions,
    Node,
    NodePosition,
    Order,
)
from vda5050_common.time import now_iso8601
from vda5050_common.topics import PROTOCOL_VERSION

from vda5050_master.fleet import Agv


def build_order(
    agv: Agv,
    waypoints: List[Tuple[float, float]],
    header_id: int,
    map_id: str = "demo-map",
) -> Order:
    nodes: List[Node] = []
    edges: List[Edge] = []
    for i, (x, y) in enumerate(waypoints):
        nodes.append(
            Node(
                nodeId=f"node-{i}",
                sequenceId=i * 2,
                released=True,
                nodePosition=NodePosition(x=x, y=y, mapId=map_id, allowedDeviationXY=0.1),
                actions=[],
            )
        )
        if i > 0:
            edges.append(
                Edge(
                    edgeId=f"edge-{i - 1}",
                    sequenceId=i * 2 - 1,
                    released=True,
                    startNodeId=f"node-{i - 1}",
                    endNodeId=f"node-{i}",
                    actions=[],
                )
            )

    return Order(
        headerId=header_id,
        timestamp=now_iso8601(),
        version=PROTOCOL_VERSION,
        manufacturer=agv.manufacturer,
        serialNumber=agv.serial_number,
        orderId=str(uuid.uuid4()),
        orderUpdateId=0,
        nodes=nodes,
        edges=edges,
    )


def build_instant_actions(
    agv: Agv,
    action_type: str,
    header_id: int,
    params: Optional[List[ActionParameter]] = None,
) -> InstantActions:
    action = Action(
        actionType=action_type,
        actionId=str(uuid.uuid4()),
        blockingType=BlockingType.HARD,
        actionParameters=params,
    )
    return InstantActions(
        headerId=header_id,
        timestamp=now_iso8601(),
        version=PROTOCOL_VERSION,
        manufacturer=agv.manufacturer,
        serialNumber=agv.serial_number,
        actions=[action],
    )
