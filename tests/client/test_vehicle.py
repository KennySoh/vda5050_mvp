from vda5050_common.models import Action, BlockingType, Edge, Node, NodePosition, Order

from vda5050_client.actions import ActionRunner
from vda5050_client.orders import ClientOrderState
from vda5050_client.vehicle import Vehicle

HEADER = {
    "headerId": 1,
    "timestamp": "2026-06-16T12:00:00.000Z",
    "version": "2.1.0",
    "manufacturer": "KIT",
    "serialNumber": "0001",
}


def make_order(waypoints, node_actions=None):
    node_actions = node_actions or {}
    nodes = [
        Node(
            nodeId=f"node-{i}",
            sequenceId=i * 2,
            released=True,
            nodePosition=NodePosition(x=x, y=y, mapId="demo-map", allowedDeviationXY=0.1),
            actions=node_actions.get(i, []),
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
    return Order(**HEADER, orderId="order-1", orderUpdateId=0, nodes=nodes, edges=edges)


def test_vehicle_traverses_to_completion():
    orders = ClientOrderState()
    actions = ActionRunner()
    vehicle = Vehicle(orders, actions, speed=1.0)

    order = make_order([(0.0, 0.0), (1.0, 0.0)])
    orders.apply_order(order)

    for _ in range(30):
        actions.tick_actions()
        vehicle.tick(dt=0.1)
        if orders.next_node() is None:
            break

    assert orders.last_node_id == "node-1"
    assert orders.next_node() is None


def test_vehicle_pauses_while_blocking_action_runs():
    orders = ClientOrderState()
    actions = ActionRunner()
    vehicle = Vehicle(orders, actions, speed=1.0)

    blocking_action = Action(actionType="pick", actionId="a1", blockingType=BlockingType.HARD)
    order = make_order([(0.0, 0.0), (1.0, 0.0)], node_actions={0: [blocking_action]})
    orders.apply_order(order)

    # Reach node-0 immediately (vehicle starts there), which starts the blocking action.
    actions.tick_actions()
    vehicle.tick(dt=0.1)
    assert orders.last_node_id == "node-0"
    assert actions.is_driving_blocked() is True

    pose_before = (vehicle.pose.x, vehicle.pose.y)
    for _ in range(5):
        actions.tick_actions()
        if not actions.is_driving_blocked():
            break
        vehicle.tick(dt=0.1)

    assert (vehicle.pose.x, vehicle.pose.y) == pose_before  # never moved while blocked

    moved = False
    for _ in range(20):
        actions.tick_actions()
        if vehicle.tick(dt=0.1):
            moved = True
            break

    assert moved is True
    assert orders.last_node_id == "node-1"
