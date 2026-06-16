from __future__ import annotations

import logging
import threading
import time

from vda5050_client.main import ClientApp
from vda5050_master.main import MasterApp
from vda5050_master.master import OrderPhase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

MANUFACTURER = "KIT"
SERIAL_NUMBER = "0001"
BROKER_PORT = 18830
WAYPOINTS = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0)]  # long route so cancel arrives mid-traversal

client = ClientApp(manufacturer=MANUFACTURER, serial_number=SERIAL_NUMBER, port=BROKER_PORT)
master = MasterApp(port=BROKER_PORT)

client.start()
master.start()

stop = threading.Event()


def tick_loop():
    while not stop.is_set():
        client.tick(dt=0.1)
        time.sleep(0.1)


threading.Thread(target=tick_loop, daemon=True).start()
time.sleep(1.0)

agv_id = f"{MANUFACTURER}/{SERIAL_NUMBER}"
master.assign_order(agv_id, WAYPOINTS)
time.sleep(1.0)  # let it start driving

pose_before_cancel = (client.vehicle.pose.x, client.vehicle.pose.y)
print(f"pose before cancel: {pose_before_cancel}")
master.cancel_order(agv_id)
time.sleep(1.0)
pose_after_cancel = (client.vehicle.pose.x, client.vehicle.pose.y)
print(f"pose after cancel + 1s: {pose_after_cancel}")

assert client.orders.has_active_order() is False, "client should be idle after cancel"
assert pose_before_cancel != (0.0, 0.0), "vehicle should have moved before cancel arrived"
assert abs(pose_after_cancel[0] - pose_before_cancel[0]) < 0.2, "vehicle should stop moving after cancel"

time.sleep(0.5)
print(f"master order_phase after cancel: {master.order_phase(agv_id)}")
assert master.order_phase(agv_id) == OrderPhase.COMPLETED, "master should see the cancel-induced completion"

stop.set()
client.stop()
print("CANCEL MID-ROUTE CHECK PASSED")
