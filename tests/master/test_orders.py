from vda5050_master.fleet import Agv
from vda5050_master.orders import build_instant_actions, build_order


def make_agv():
    return Agv(manufacturer="KIT", serial_number="0001")


def test_build_order_creates_one_node_per_waypoint():
    order = build_order(make_agv(), [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], header_id=1)
    assert len(order.nodes) == 3
    assert len(order.edges) == 2
    assert order.headerId == 1
    assert order.orderUpdateId == 0
    assert order.manufacturer == "KIT"
    assert order.serialNumber == "0001"


def test_build_order_edges_connect_nodes_in_sequence():
    order = build_order(make_agv(), [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], header_id=1)
    for i, edge in enumerate(order.edges):
        assert edge.startNodeId == order.nodes[i].nodeId
        assert edge.endNodeId == order.nodes[i + 1].nodeId


def test_build_order_all_nodes_and_edges_released_in_v0():
    order = build_order(make_agv(), [(0.0, 0.0), (1.0, 0.0)], header_id=1)
    assert all(node.released for node in order.nodes)
    assert all(edge.released for edge in order.edges)


def test_build_instant_actions_creates_single_action():
    instant_actions = build_instant_actions(make_agv(), "cancelOrder", header_id=1)
    assert len(instant_actions.actions) == 1
    assert instant_actions.actions[0].actionType == "cancelOrder"
