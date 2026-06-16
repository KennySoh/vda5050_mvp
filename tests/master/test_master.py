from vda5050_common.models import (
    ActionState,
    ActionStatus,
    BatteryState,
    EStop,
    Error,
    ErrorLevel,
    OperatingMode,
    SafetyState,
    State,
)

from vda5050_master.fleet import Fleet
from vda5050_master.master import AssignmentDecision, Master, OrderPhase

HEADER = {
    "headerId": 1,
    "timestamp": "2026-06-16T12:00:00.000Z",
    "version": "2.1.0",
    "manufacturer": "KIT",
    "serialNumber": "0001",
}


def make_master():
    fleet = Fleet()
    published_orders = []
    published_instant_actions = []
    master = Master(
        fleet,
        publish_order=lambda agv, order: published_orders.append((agv, order)),
        publish_instant_actions=lambda agv, actions: published_instant_actions.append((agv, actions)),
    )
    return fleet, master, published_orders, published_instant_actions


def make_state(order_id="order-1", node_states=(), edge_states=(), action_states=(), errors=(), new_base_request=False):
    return State(
        **HEADER,
        orderId=order_id,
        orderUpdateId=0,
        lastNodeId="",
        lastNodeSequenceId=0,
        nodeStates=list(node_states),
        edgeStates=list(edge_states),
        driving=False,
        newBaseRequest=new_base_request,
        actionStates=list(action_states),
        batteryState=BatteryState(batteryCharge=100.0, charging=False),
        operatingMode=OperatingMode.AUTOMATIC,
        errors=list(errors),
        safetyState=SafetyState(eStop=EStop.NONE, fieldViolation=False),
    )


def test_assign_order_rejects_unknown_agv():
    _, master, published_orders, _ = make_master()
    assignment_id, decision = master.assign_order("KIT/0001", [(0.0, 0.0)])
    assert decision == AssignmentDecision.REJECTED_PREFLIGHT
    assert published_orders == []
    assert assignment_id


def test_assign_order_accepts_known_agv():
    fleet, master, published_orders, _ = make_master()
    agv = fleet.get_or_create("KIT", "0001")
    assignment_id, decision = master.assign_order(agv.agv_id, [(0.0, 0.0), (1.0, 0.0)])
    assert decision == AssignmentDecision.ACCEPTED
    assert len(published_orders) == 1
    assert agv.current_order_id != ""
    assert master.order_phase(agv) == OrderPhase.ACCEPTED


def test_on_state_detects_completion():
    fleet, master, _, _ = make_master()
    agv = fleet.get_or_create("KIT", "0001")
    agv.current_order_id = "order-1"

    state = make_state(
        action_states=[
            ActionState(actionId="a1", actionStatus=ActionStatus.FINISHED),
        ]
    )
    master.on_state(agv, state)

    assert master.order_phase(agv) == OrderPhase.COMPLETED
    assert agv.current_order_id == ""


def test_on_state_records_progress_when_not_complete():
    fleet, master, _, _ = make_master()
    agv = fleet.get_or_create("KIT", "0001")
    agv.current_order_id = "order-1"

    from vda5050_common.models import NodeState

    state = make_state(node_states=[NodeState(nodeId="node-1", sequenceId=0, released=True)])
    master.on_state(agv, state)

    assert master.order_phase(agv) == OrderPhase.RUNNING
    assert agv.current_order_id == "order-1"


def test_on_state_detects_fatal_error():
    fleet, master, _, _ = make_master()
    agv = fleet.get_or_create("KIT", "0001")
    agv.current_order_id = "order-1"

    from vda5050_common.models import NodeState

    state = make_state(
        node_states=[NodeState(nodeId="node-1", sequenceId=0, released=True)],
        errors=[Error(errorType="someError", errorLevel=ErrorLevel.FATAL)],
    )
    master.on_state(agv, state)

    assert master.order_phase(agv) == OrderPhase.FAILED


def test_cancel_order_publishes_instant_actions():
    fleet, master, _, published_instant_actions = make_master()
    agv = fleet.get_or_create("KIT", "0001")
    agv.current_order_id = "order-1"

    master.cancel_order(agv)

    assert len(published_instant_actions) == 1
    _, instant_actions = published_instant_actions[0]
    assert instant_actions.actions[0].actionType == "cancelOrder"
