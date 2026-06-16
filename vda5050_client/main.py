from __future__ import annotations

import logging

from vda5050_common.models import (
    Action,
    AgvClass,
    AgvKinematic,
    Error,
    ErrorLevel,
    ErrorReference,
    Factsheet,
    InstantActions,
    Order,
    TypeSpecification,
)
from vda5050_common.time import now_iso8601
from vda5050_common.topics import PROTOCOL_VERSION

from vda5050_client.actions import ActionRunner
from vda5050_client.mqtt import ClientMqtt
from vda5050_client.orders import ClientOrderState
from vda5050_client.state import StateBuilder
from vda5050_client.vehicle import Vehicle

logger = logging.getLogger(__name__)


def _build_demo_factsheet(manufacturer: str, serial_number: str) -> Factsheet:
    return Factsheet(
        headerId=0,
        timestamp=now_iso8601(),
        version=PROTOCOL_VERSION,
        manufacturer=manufacturer,
        serialNumber=serial_number,
        typeSpecification=TypeSpecification(
            seriesName="vda5050-mvp-demo",
            agvKinematic=AgvKinematic.DIFF,
            agvClass=AgvClass.CARRIER,
            maxLoadMass=50.0,
            localizationTypes=["NATURAL"],
            navigationTypes=["AUTONOMOUS"],
        ),
    )


class ClientApp:
    def __init__(
        self,
        manufacturer: str,
        serial_number: str,
        host: str = "127.0.0.1",
        port: int = 1883,
    ) -> None:
        self.manufacturer = manufacturer
        self.serial_number = serial_number
        self.orders = ClientOrderState()
        self.actions = ActionRunner()
        self.vehicle = Vehicle(self.orders, self.actions)
        self.state_builder = StateBuilder(
            manufacturer, serial_number, f"uagv/v2/{manufacturer}/{serial_number}/state"
        )
        self.mqtt = ClientMqtt(manufacturer, serial_number, host=host, port=port)
        self.mqtt.on_order(self._handle_order)
        self.mqtt.on_instant_actions(self._handle_instant_actions)

    def start(self) -> None:
        factsheet = _build_demo_factsheet(self.manufacturer, self.serial_number)
        self.mqtt.connect(factsheet)
        logger.info(
            "event=client.started manufacturer=%s serial_number=%s",
            self.manufacturer,
            self.serial_number,
        )

    def tick(self, dt: float = 0.1) -> None:
        self.actions.tick_actions()
        node_reached = self.vehicle.tick(dt)
        if node_reached:
            self.state_builder.mark_dirty("node_reached")
        if self.orders.has_active_order() and self.orders.check_newly_completed(
            self.actions.action_states()
        ):
            self.state_builder.mark_dirty("order_completed")
            logger.info("event=order.completed order_id=%s", self.orders.order_id)
        if self.state_builder.should_publish():
            self._publish_state()

    def stop(self) -> None:
        self.mqtt.stop()

    def run_forever(self, dt: float = 0.1) -> None:
        import time

        self.start()
        try:
            while True:
                self.tick(dt)
                time.sleep(dt)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _handle_order(self, order: Order) -> None:
        rejection = self.orders.accept_or_reject(
            order, current_position=(self.vehicle.pose.x, self.vehicle.pose.y)
        )
        if rejection is not None:
            self.state_builder.add_error(rejection)
            logger.info(
                "event=order.rejected order_id=%s reason=%s", order.orderId, rejection.errorType
            )
            return
        self.orders.apply_order(order)
        self.state_builder.mark_dirty("order_accepted")
        logger.info("event=order.accepted order_id=%s", order.orderId)

    def _handle_instant_actions(self, instant_actions: InstantActions) -> None:
        for action in instant_actions.actions:
            if action.actionType == "cancelOrder":
                self._handle_cancel_order(action)
            else:
                logger.info(
                    "event=instant_actions.unsupported action_type=%s (not implemented yet)",
                    action.actionType,
                )

    def _handle_cancel_order(self, action: Action) -> None:
        if not self.orders.has_active_order():
            error = Error(
                errorType="noOrderToCancel",
                errorLevel=ErrorLevel.WARNING,
                errorDescription="no order to cancel",
                errorReferences=[ErrorReference(referenceKey="actionId", referenceValue=action.actionId)],
            )
            self.state_builder.add_error(error)
            logger.info("event=cancel.failed reason=no_active_order")
            return
        self.actions.fail_all_running()
        self.orders.cancel_order()
        self.state_builder.mark_dirty("cancel_applied")
        logger.info("event=cancel.applied order_id=%s", self.orders.order_id)

    def _publish_state(self) -> None:
        state = self.state_builder.build_state(self.orders, self.vehicle, self.actions)
        self.mqtt.publish_state(state)
        self.state_builder.clear_dirty()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    app = ClientApp(manufacturer="KIT", serial_number="0001")
    app.run_forever()
