from vda5050_common.models import Edge, Node, NodePosition, Order

from vda5050_client.orders import ClientOrderState

HEADER = {
    "headerId": 1,
    "timestamp": "2026-06-16T12:00:00.000Z",
    "version": "2.1.0",
    "manufacturer": "KIT",
    "serialNumber": "0001",
}


def make_order(order_id="order-1", order_update_id=0, start=(0.0, 0.0), waypoints=((0.0, 0.0), (1.0, 0.0))):
    nodes = [
        Node(
            nodeId=f"node-{i}",
            sequenceId=i * 2,
            released=True,
            nodePosition=NodePosition(x=x, y=y, mapId="demo-map", allowedDeviationXY=0.1),
            actions=[],
        )
        for i, (x, y) in enumerate(waypoints)
    ]
    edges = [
        Edge(
            edgeId=f"edge-{i}",
            sequenceId=i * 2 + 1,
            released=True,
            startNodeId=f"node-{i}",
            endNodeId=f"node-{i + 1}",
            actions=[],
        )
        for i in range(len(nodes) - 1)
    ]
    return Order(**HEADER, orderId=order_id, orderUpdateId=order_update_id, nodes=nodes, edges=edges)


def test_accepts_valid_order_from_current_position():
    orders = ClientOrderState()
    order = make_order()
    assert orders.accept_or_reject(order, current_position=(0.0, 0.0)) is None
    orders.apply_order(order)
    assert orders.has_active_order()
    assert orders.next_node().nodeId == "node-0"


def test_rejects_order_with_no_nodes():
    orders = ClientOrderState()
    order = make_order()
    order.nodes = []
    order.edges = []
    rejection = orders.accept_or_reject(order, current_position=(0.0, 0.0))
    assert rejection is not None
    assert rejection.errorType == "validationError"


def test_rejects_unreachable_first_node():
    orders = ClientOrderState()
    order = make_order(waypoints=((100.0, 100.0), (101.0, 100.0)))
    rejection = orders.accept_or_reject(order, current_position=(0.0, 0.0))
    assert rejection is not None
    assert rejection.errorType == "orderError"


def test_rejects_order_when_already_busy_with_a_different_order():
    orders = ClientOrderState()
    first = make_order(order_id="order-1")
    orders.apply_order(first)
    second = make_order(order_id="order-2")
    rejection = orders.accept_or_reject(second, current_position=(0.0, 0.0))
    assert rejection is not None
    assert rejection.errorType == "orderError"


def test_rejects_stale_order_update_id():
    orders = ClientOrderState()
    first = make_order(order_id="order-1", order_update_id=1)
    orders.apply_order(first)
    stale_update = make_order(order_id="order-1", order_update_id=0)
    rejection = orders.accept_or_reject(stale_update, current_position=(0.0, 0.0))
    assert rejection is not None
    assert rejection.errorType == "orderUpdateError"


def test_rejects_mismatched_edge_sequence():
    orders = ClientOrderState()
    order = make_order()
    order.edges[0].startNodeId = "node-99"
    rejection = orders.accept_or_reject(order, current_position=(0.0, 0.0))
    assert rejection is not None
    assert rejection.errorType == "validationError"


def test_traversal_and_completion():
    orders = ClientOrderState()
    order = make_order(waypoints=((0.0, 0.0), (1.0, 0.0)))
    orders.apply_order(order)
    assert orders.is_order_complete([]) is False

    orders.mark_node_reached("node-0")
    assert orders.next_node().nodeId == "node-1"
    assert [n.nodeId for n in orders.node_states()] == ["node-1"]
    assert [e.edgeId for e in orders.edge_states()] == ["edge-0"]  # left once node-1 is reached

    orders.mark_node_reached("node-1")
    assert orders.next_node() is None
    assert orders.node_states() == []
    assert orders.edge_states() == []
    assert orders.last_node_id == "node-1"


def test_cancel_order_clears_remaining_progress_but_keeps_order_id():
    orders = ClientOrderState()
    order = make_order(waypoints=((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)))
    orders.apply_order(order)
    orders.mark_node_reached("node-0")

    orders.cancel_order()

    assert orders.node_states() == []
    assert orders.edge_states() == []
    assert orders.order_id == order.orderId
    assert orders.is_order_complete([]) is True
