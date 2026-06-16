# VDA5050 MVP — Implementation Checklist

Actionable, step-by-step companion to `docs/design_doc.md` (the architecture/design
doc). Work top to bottom — each phase only makes sense once the previous
one's checklist is done. Section numbers in parentheses point back to the
matching `docs/design_doc.md` section.

Some checklist items below introduce `AssignmentDecision`, `OrderPhase`,
and `MasterConnectionState` — these are not VDA5050 spec terms, they're
borrowed from `rmf2_device_manager`'s VDA5050 Master Device Controller
design so this prototype's `master.py` shapes port forward cleanly. Full
rationale and exact enum values: `docs/design_doc.md` §13.

---

## 0. Scaffolding

- [x] `pyproject.toml` — deps: `pydantic`, `paho-mqtt`, `pytest`
- [x] `docker-compose.yml` — single Mosquitto service. Host port **18830**,
      not the spec-irrelevant default 1883 — this machine already has an
      unrelated system Mosquitto bound to 1883/1884, so the compose
      service maps `18830:1883` to avoid colliding with it. Connect at
      `127.0.0.1:18830`.
- [x] Create empty packages: `vda5050_common/`, `vda5050_master/`,
      `vda5050_client/`, `tests/`, `examples/` (§14 folder tree)
- [x] `docker-compose up -d` and confirm the broker is reachable
      (no `mosquitto_pub`/`sub` CLI on this machine — used a `paho-mqtt`
      publish/subscribe round-trip script instead; passed)
- [x] `uv venv` + `uv pip install -e ".[dev]"` — dev environment uses
      `uv`, not a manually-managed `venv`/system pip (this machine's
      system Python is externally-managed)

---

## 1. Shared vocabulary — `vda5050_common/` (§3)

- [x] `models.py`: header fields + `Order`, `Node`, `NodePosition`, `Edge`,
      `Action`, `ActionParameter`, `InstantActions`, `State`, `NodeState`,
      `EdgeState`, `ActionState`, `BatteryState`, `Error`,
      `ErrorReference`, `Info`, `InfoReference`, `SafetyState`,
      `Connection`, `Factsheet` (minimal stub)
- [x] `topics.py`: `topic(interface, major_version, manufacturer, serial,
      name)`, `QOS` dict
- [x] `mqtt.py`: thin wrapper — `connect()`, last-will config,
      `publish(topic_name, model, retain=False)`, `subscribe(topic_name,
      callback)`
- [x] `time.py`: `next_header_id()`, `now_iso8601()`
- [x] `tests/test_models.py`: round-trip every model against a hand-built
      JSON fixture (dump → load → equal, exact camelCase field names)

**Checkpoint:** `pytest tests/test_models.py` passes with zero MQTT
imports. ✅ 5/5 passed.

> Local gotcha (this machine only, not project config): a sourced ROS2
> environment leaks a stale `PYTHONPATH` into every shell, which makes
> `pytest` try to autoload a broken `launch_testing` plugin via entry
> points. Run `PYTHONPATH= .venv/bin/python -m pytest ...` (or `uv run
> --no-sync env -u PYTHONPATH pytest`) to get a clean ROS-free
> interpreter — consistent with this project's no-ROS2 stance anyway.

---

## 2. V0 — core happy path (§11 V0)

### 2.1 Client startup / connected (§9.1)
- [x] `vda5050_client/mqtt.py`: `connect()`, publish `connection=ONLINE`,
      publish retained `factsheet`, configure last-will
      `connection=CONNECTIONBROKEN`
- [x] `vda5050_client/main.py`: wire startup, call into `mqtt.py`
- [x] `vda5050_master/fleet.py`: `Agv` dataclass; `Fleet.get_or_create()`,
      `.record_connection()`, `.record_factsheet()`
- [x] `vda5050_master/mqtt.py`: subscribe `connection`/`factsheet`,
      forward parsed messages to `fleet.py`
- [x] `vda5050_master/master.py`: `MasterConnectionState` —
      `STARTING` on boot, flip to `READY` once the master's own MQTT
      client connects (docs/design_doc.md §13; not an AGV's connection state)
- [x] Manual check: start client, start master, confirm master logs
      `AgvRegistered` and its own `MasterConnectionState` reaching
      `READY` — verified via `examples/run_demo.py`.

### 2.2 Master assigns a new order (§9.3)
- [x] `vda5050_master/orders.py`: `build_order(agv, waypoints)`
- [x] `vda5050_master/master.py`: `AssignmentDecision` enum
      (`ACCEPTED`/`REJECTED_PREFLIGHT` for now — `QUEUED`/
      `REJECTED_POSTFLIGHT` are V2, §4.1); `assign_order(agv_id,
      waypoints) -> (assignment_id, AssignmentDecision)` — generate a
      UUID `assignment_id`, return `REJECTED_PREFLIGHT` if `agv_id` isn't
      onboarded, otherwise build + send the order and return `ACCEPTED`
      (docs/design_doc.md §13)
- [x] `vda5050_master/mqtt.py`: `publish_order(agv, order)`
- [x] `vda5050_client/orders.py`: `accept_or_reject(order)` (V0 subset
      only — see §9.4 for which checks), `apply_order(order)`
- [x] `vda5050_client/mqtt.py`: subscribe `order`, forward to `orders.py`
- [x] `vda5050_client/state.py`: `mark_dirty(reason)`, minimal
      `build_state()`; publish once on acceptance

### 2.3 Traversal (§9.5)
- [x] `vda5050_client/vehicle.py`: `tick()`, `move_towards_next_node()`,
      `check_node_reached()`
- [x] `vda5050_client/orders.py`: `mark_node_reached(node_id)`,
      `next_node()`
- [x] `vda5050_client/actions.py`: `start_action()`, `tick_actions()`,
      `is_driving_blocked()` (V0 stub: `False` if no actions defined yet)
- [x] `vda5050_client/main.py`: simulation tick loop (every 100ms:
      `actions.tick_actions()` → `vehicle.tick()` →
      `state.publish_if_dirty()`)

### 2.4 State publish + completion (§9.7, §9.8)
- [x] `vda5050_client/orders.py`: `is_order_complete()`
- [x] `vda5050_client/state.py`: `should_publish()`, publish whenever
      dirty
- [x] `vda5050_master/master.py`: `OrderPhase` enum (`NO_ORDER`/
      `ACCEPTED`/`RUNNING`/`COMPLETED`/`FAILED`, docs/design_doc.md §13);
      `on_state(agv, state)` — completion check → `record_progress()`
      (the `newBaseRequest`/error branches can stay stubs until V1/V2),
      deriving/updating the AGV's current `OrderPhase` on every call
      instead of a bare completion boolean
- [x] `vda5050_master/fleet.py`: `record_state()`, `clear_current_order()`
- [x] `examples/run_demo.py`: scripted V0 demo (start client, start
      master, send one hardcoded order, wait for completion log)

**Checkpoint (V0 done):** ✅ `python -m examples.run_demo` shows, in
order: client online → master sees AGV (`agv.registered`) → order sent
(`AssignmentDecision.ACCEPTED`) → order accepted → node(s) traversed
(`order.progress` × 2) → state published → master logs order completed
(`order.completed`, `OrderPhase.COMPLETED`). Ran clean on the first try
against the local broker (`uv run`, `PYTHONPATH=` cleared — see §1 note).

---

## 3. V1 — reliability and basic control (§11 V1)

### 3.1 Order rejection (§9.4)
- [x] `vda5050_client/orders.py`: implement the full V0-rejection subset
      — wrong `orderUpdateId`, already busy with another order, invalid
      node/edge sequence, first node unreachable
- [x] `vda5050_client/state.py`: `add_error(error)`
- [x] Test: send a deliberately invalid order, assert rejection + error
      appears in published `state` — `tests/client/test_orders.py`
      (7 rejection/acceptance cases, zero MQTT imports).

### 3.2 Disconnect handling (§9.2)
- [x] `vda5050_client/mqtt.py`: confirm last-will fires on unexpected
      kill; `stop()` publishes `connection=OFFLINE` then disconnects
      cleanly
- [x] `vda5050_master/fleet.py`: `mark_unreachable(agv)`
- [x] `vda5050_master/master.py`: `on_connection(agv, connection)` (per-AGV);
      separately, flip the master's own `MasterConnectionState` to
      `DEGRADED` if *the master's* MQTT client disconnects from the
      broker (distinct from any single AGV going `CONNECTIONBROKEN`), and
      to `SHUTTING_DOWN` on graceful master exit (docs/design_doc.md §13)
- [x] Test: kill the client process — master marks that AGV unreachable
      but its own `MasterConnectionState` stays `READY` (the broker
      connection itself is fine). Separately, test graceful client
      `stop()` — no `CONNECTIONBROKEN` last-will fires. Separately, stop
      the broker — master's own `MasterConnectionState` flips to
      `DEGRADED`.
      ✅ All three run manually as separate OS processes (`kill -9` on
      the client; `docker compose stop/start mosquitto` on the broker)
      against the real broker — exactly as the checklist describes, log
      output confirmed each transition.

### 3.3 `cancelOrder` (§9.10)
- [x] `vda5050_master/orders.py`: `build_instant_actions(agv,
      "cancelOrder")`
- [x] `vda5050_master/master.py`: `cancel_order(agv)`
- [x] `vda5050_client/orders.py`: `cancel_order()` (Figure 9 behavior)
- [x] `vda5050_client/actions.py`: `fail_all_running()`
- [x] `vda5050_client/mqtt.py`: subscribe `instantActions`
- [x] Test: send `cancelOrder` mid-route, assert vehicle stops and state
      reflects the cancellation — `tests/master/test_master.py`
      (`cancel_order` publishes `cancelOrder`) plus a real end-to-end
      MQTT run (`examples/manual_cancel_check.py`): order assigned,
      cancelled 1s into a 3-node route, vehicle stops in place, client
      reports idle, master sees `OrderPhase.COMPLETED`.

### 3.4 Action blocking (§9.6)
- [x] `vda5050_client/actions.py`: real `is_driving_blocked()` — `NONE`
      doesn't block, `SOFT`/`HARD` both do (V0/V1 simplification)
- [x] `vda5050_client/vehicle.py`: skip movement this tick when blocked
- [x] Test: order with a blocking action on a node, assert the vehicle
      pauses until the action finishes —
      `tests/client/test_vehicle.py::test_vehicle_pauses_while_blocking_action_runs`.

### 3.5 Heartbeat (§9.12)
- [x] `vda5050_client/state.py`: heartbeat timer (1s for easy debugging)
- [x] Test: idle client with no state changes still publishes on the
      heartbeat interval — verified directly against `StateBuilder`
      (should_publish() flips true once the interval elapses with
      nothing marked dirty).

**Checkpoint (V1 done):** ✅ all of §2's V0 checkpoint plus rejection,
disconnect, cancel, and blocking-action scenarios pass. 35/35 pytest
(`tests/`), plus the three manual disconnect scenarios and the manual
cancel-mid-route scenario, all verified against the real broker.

> Found and fixed along the way: `master.py`'s order-completion handler
> originally re-fired `event=order.completed` and `clear_current_order`
> on *every* heartbeat after completion (since the client keeps
> reporting the same completed `orderId`/empty `nodeStates` forever, per
> spec). Added a small idempotency guard so it only fires once per
> completion — pure noise reduction, no behavior change.

---

## 4. V2 — full spec correctness (§11 V2)

### 4.1 Order update / stitching node (§9.11)
- [ ] `vda5050_master/orders.py`: `build_order_update()` — increment
      `orderUpdateId`, include the stitching node, extend/replace horizon
- [ ] `vda5050_client/orders.py`: `accept_or_reject()` handles order
      updates — validate stitching node matches current decision point
- [ ] `vda5050_master/master.py`: when a stitch isn't yet possible (AGV
      hasn't reached the decision point yet), return
      `AssignmentDecision.QUEUED` instead of blocking, and hold the
      pending update in a small per-AGV queue (`pending_stitch_count`,
      mirroring `OrderStatus.pending_stitch_count` — docs/design_doc.md §13);
      drain it as the AGV's state progresses
- [ ] Test: send an order update mid-route, assert it's accepted and the
      base/horizon extends correctly
- [ ] Test: send an order update before the AGV reaches the decision
      point, assert `AssignmentDecision.QUEUED` and that it's applied
      automatically once the AGV catches up

### 4.2 `newBaseRequest` (§9.9)
- [ ] `vda5050_client/state.py`: set `newBaseRequest=true` when nearing
      the end of the current base
- [ ] `vda5050_master/master.py`: `handle_new_base_request()` →
      `orders.build_order_update()`
- [ ] Test: long multi-segment order, assert the horizon auto-extends
      without operator intervention

### 4.3 Full Figure 8 acceptance tree
- [ ] Add the remaining branches beyond the V0/V1 subset: deprecated
      `orderUpdateId` detection, duplicate-update detection (same
      `orderId`+`orderUpdateId` twice → silently discard), continuation-
      of-just-completed-order check
- [ ] `vda5050_master/master.py`: `AssignmentDecision.REJECTED_POSTFLIGHT`
      stays reserved/unemitted for now (same as the rmf2_device_manager
      reference design) — note where it *would* hook in (e.g. a factsheet
      change invalidating an already-`ACCEPTED`/`QUEUED` order) without
      implementing it yet

### 4.4 Full Figure 17 blocking-type behavior
- [ ] `vda5050_client/actions.py`: real parallel-execution-list handling
      for `NONE`/`SOFT` actions running together; `HARD` actions flush the
      queue and run alone

### 4.5 Better error handling
- [ ] Populate `errorReferences[]` consistently across every
      rejection/failure path (headerId, topic, orderId/orderUpdateId,
      actionId — per spec §7.1)
- [ ] Switch the heartbeat to the spec's real 30s default (configurable,
      keep 1s available for local debugging)

**Checkpoint (V2 done):** full regression across every scenario in
`docs/design_doc.md` §9.

---

## 5. Explicitly out of scope (tracked, not required)

- [ ] `visualization` topic
- [ ] Maps (`downloadMap`/`enableMap`/`deleteMap`)
- [ ] `corridor` / `trajectory` (NURBS)
- [ ] Multi-AGV fleet/traffic management — when this happens, onboard via
      a `FleetRoster`-style full-state diff (present-but-not-local →
      onboard, local-but-not-present → offboard) rather than ad hoc
      add/remove calls; see docs/design_doc.md §13
- [ ] `zoneSetId`
- [ ] Full `factsheet` detail (beyond the MVP stub)
- [ ] Real robot driver behind `vehicle.py`'s interface
