from __future__ import annotations

import logging
import threading
import time

from vda5050_client.main import ClientApp
from vda5050_master.main import MasterApp
from vda5050_master.master import OrderPhase

logger = logging.getLogger(__name__)

MANUFACTURER = "KIT"
SERIAL_NUMBER = "0001"
WAYPOINTS = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]

# This machine's docker-compose maps the demo broker to host port 18830
# (port 1883 is already taken by an unrelated system service) — see plan.md §0.
BROKER_PORT = 18830


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    client = ClientApp(manufacturer=MANUFACTURER, serial_number=SERIAL_NUMBER, port=BROKER_PORT)
    master = MasterApp(port=BROKER_PORT)

    client.start()
    master.start()

    stop_ticking = threading.Event()

    def tick_loop() -> None:
        while not stop_ticking.is_set():
            client.tick(dt=0.1)
            time.sleep(0.1)

    ticker = threading.Thread(target=tick_loop, daemon=True)
    ticker.start()

    time.sleep(1.0)  # let connection/factsheet/registration settle

    agv_id = f"{MANUFACTURER}/{SERIAL_NUMBER}"
    assignment_id, decision = master.assign_order(agv_id, WAYPOINTS)
    logger.info("event=demo.order_assigned assignment_id=%s decision=%s", assignment_id, decision)

    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if master.order_phase(agv_id) == OrderPhase.COMPLETED:
            logger.info("event=demo.order_completed")
            break
        time.sleep(0.2)
    else:
        logger.warning("event=demo.timeout")

    stop_ticking.set()
    ticker.join(timeout=2.0)
    client.stop()


if __name__ == "__main__":
    main()
