from __future__ import annotations

from typing import Callable

import paho.mqtt.client as mqtt
from pydantic import BaseModel

from vda5050_common.topics import QOS


def _qos_for(topic_name: str) -> int:
    return QOS[topic_name.rsplit("/", 1)[-1]]


class MqttConnection:
    def __init__(self, client_id: str, host: str = "127.0.0.1", port: int = 1883):
        self._host = host
        self._port = port
        self._subscriptions: list[str] = []
        self._on_connected_callbacks: list[Callable[[], None]] = []
        self._on_disconnected_callbacks: list[Callable[[], None]] = []
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def on_connected(self, callback: Callable[[], None]) -> None:
        self._on_connected_callbacks.append(callback)

    def on_disconnected(self, callback: Callable[[], None]) -> None:
        self._on_disconnected_callbacks.append(callback)

    def set_last_will(self, topic_name: str, model: BaseModel, retain: bool = True) -> None:
        self._client.will_set(
            topic_name,
            model.model_dump_json(exclude_none=True),
            qos=_qos_for(topic_name),
            retain=retain,
        )

    def connect(self) -> None:
        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, topic_name: str, model: BaseModel, retain: bool = False) -> None:
        self._client.publish(
            topic_name,
            model.model_dump_json(exclude_none=True),
            qos=_qos_for(topic_name),
            retain=retain,
        )

    def subscribe(self, topic_filter: str, callback: Callable[[bytes], None]) -> None:
        self._client.message_callback_add(
            topic_filter, lambda client, userdata, msg: callback(msg.payload)
        )
        self._subscriptions.append(topic_filter)
        self._client.subscribe(topic_filter, qos=_qos_for(topic_filter))

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        for topic_filter in self._subscriptions:
            self._client.subscribe(topic_filter, qos=_qos_for(topic_filter))
        for callback in self._on_connected_callbacks:
            callback()

    def _on_disconnect(self, client, userdata, *args) -> None:
        for callback in self._on_disconnected_callbacks:
            callback()
