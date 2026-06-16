from vda5050_common.models import Connection, ConnectionState

from vda5050_master.fleet import Fleet

HEADER = {
    "headerId": 1,
    "timestamp": "2026-06-16T12:00:00.000Z",
    "version": "2.1.0",
    "manufacturer": "KIT",
    "serialNumber": "0001",
}


def test_get_or_create_returns_same_agv_for_same_identity():
    fleet = Fleet()
    first = fleet.get_or_create("KIT", "0001")
    second = fleet.get_or_create("KIT", "0001")
    assert first is second
    assert first.agv_id == "KIT/0001"


def test_get_or_create_creates_distinct_agvs_for_distinct_identities():
    fleet = Fleet()
    a = fleet.get_or_create("KIT", "0001")
    b = fleet.get_or_create("KIT", "0002")
    assert a is not b


def test_mark_unreachable_on_connection_broken():
    fleet = Fleet()
    agv = fleet.get_or_create("KIT", "0001")
    fleet.record_connection(
        agv, Connection(**HEADER, connectionState=ConnectionState.CONNECTIONBROKEN)
    )
    fleet.mark_unreachable(agv)
    assert agv.reachable is False


def test_record_connection_online_marks_reachable_again():
    fleet = Fleet()
    agv = fleet.get_or_create("KIT", "0001")
    fleet.mark_unreachable(agv)
    fleet.record_connection(agv, Connection(**HEADER, connectionState=ConnectionState.ONLINE))
    assert agv.reachable is True


def test_clear_current_order():
    fleet = Fleet()
    agv = fleet.get_or_create("KIT", "0001")
    agv.current_order_id = "order-1"
    agv.current_order_update_id = 3
    fleet.clear_current_order(agv)
    assert agv.current_order_id == ""
    assert agv.current_order_update_id == 0
