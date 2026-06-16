import json

from vda5050_common.models import (
    Action,
    BatteryState,
    Connection,
    Edge,
    Factsheet,
    InstantActions,
    Node,
    NodePosition,
    Order,
    SafetyState,
    State,
    TypeSpecification,
)

HEADER = {
    "headerId": 1,
    "timestamp": "2026-06-16T12:00:00.000Z",
    "version": "2.1.0",
    "manufacturer": "KIT",
    "serialNumber": "0001",
}


def test_order_round_trip():
    fixture = {
        **HEADER,
        "orderId": "order-1",
        "orderUpdateId": 0,
        "nodes": [
            {
                "nodeId": "node-1",
                "sequenceId": 0,
                "released": True,
                "nodePosition": {"x": 1.0, "y": 2.0, "mapId": "map-1"},
                "actions": [
                    {
                        "actionType": "pick",
                        "actionId": "action-1",
                        "blockingType": "HARD",
                        "actionParameters": [{"key": "loadType", "value": "pallet"}],
                    }
                ],
            },
            {"nodeId": "node-2", "sequenceId": 2, "released": True, "actions": []},
        ],
        "edges": [
            {
                "edgeId": "edge-1",
                "sequenceId": 1,
                "released": True,
                "startNodeId": "node-1",
                "endNodeId": "node-2",
                "actions": [],
            }
        ],
    }

    order = Order.model_validate(fixture)
    dumped = json.loads(order.model_dump_json(exclude_none=True))
    assert dumped == fixture
    assert isinstance(order.nodes[0], Node)
    assert isinstance(order.nodes[0].nodePosition, NodePosition)
    assert isinstance(order.nodes[0].actions[0], Action)
    assert isinstance(order.edges[0], Edge)


def test_instant_actions_round_trip():
    fixture = {
        **HEADER,
        "actions": [
            {"actionType": "cancelOrder", "actionId": "action-2", "blockingType": "HARD"}
        ],
    }

    instant_actions = InstantActions.model_validate(fixture)
    dumped = json.loads(instant_actions.model_dump_json(exclude_none=True))
    assert dumped == fixture


def test_state_round_trip():
    fixture = {
        **HEADER,
        "orderId": "order-1",
        "orderUpdateId": 0,
        "lastNodeId": "node-1",
        "lastNodeSequenceId": 0,
        "nodeStates": [],
        "edgeStates": [],
        "driving": True,
        "actionStates": [],
        "batteryState": {"batteryCharge": 80.0, "charging": False},
        "operatingMode": "AUTOMATIC",
        "errors": [],
        "safetyState": {"eStop": "NONE", "fieldViolation": False},
    }

    state = State.model_validate(fixture)
    dumped = json.loads(state.model_dump_json(exclude_none=True))
    assert dumped == fixture
    assert isinstance(state.batteryState, BatteryState)
    assert isinstance(state.safetyState, SafetyState)


def test_connection_round_trip():
    fixture = {**HEADER, "connectionState": "ONLINE"}
    connection = Connection.model_validate(fixture)
    dumped = json.loads(connection.model_dump_json(exclude_none=True))
    assert dumped == fixture


def test_factsheet_round_trip():
    fixture = {
        **HEADER,
        "typeSpecification": {
            "seriesName": "demo-series",
            "agvKinematic": "DIFF",
            "agvClass": "CARRIER",
            "maxLoadMass": 50.0,
            "localizationTypes": ["NATURAL"],
            "navigationTypes": ["AUTONOMOUS"],
        },
    }
    factsheet = Factsheet.model_validate(fixture)
    dumped = json.loads(factsheet.model_dump_json(exclude_none=True))
    assert dumped == fixture
    assert isinstance(factsheet.typeSpecification, TypeSpecification)
