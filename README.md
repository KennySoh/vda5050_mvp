# VDA5050 Master + Client — Quickstart

A Python VDA5050 v2.1.0 master and client, talking over plain MQTT (no
ROS2). This is the quickstart — for the architecture, module
responsibilities, and design rationale, read `docs/design_doc.md`. For the
step-by-step implementation checklist, see `plan.md`.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Docker (for the local Mosquitto broker)

## 1. Install dependencies

```bash
uv venv
uv pip install -e ".[dev]"
```

## 2. Start the broker

```bash
docker compose up -d
```

This starts Mosquitto on `localhost:18830` (not the default 1883 — see
the note in `docker-compose.yml` / `plan.md` §0 if you need to change
it).

## 3. Run the demo

```bash
PYTHONPATH= .venv/bin/python -m examples.run_demo
```

This starts one simulated client (AGV) and one master in a single
process, assigns a 3-waypoint order, and logs the full lifecycle:
client online → master registers the AGV → order sent → order accepted
→ traversal → order completed.

> Note: if your shell has a ROS2 environment sourced, it can leak a
> stale `PYTHONPATH` that breaks Python tooling here. Clearing it
> (`PYTHONPATH=`) keeps this project's interpreter ROS-free, which is
> intentional — see `plan.md` §1.

## 4. Run the tests

```bash
PYTHONPATH= .venv/bin/python -m pytest tests/ -v
```

All tests run against the models/logic directly with zero MQTT
imports — no broker needed.

## 5. Run client and master as separate processes

```bash
# terminal 1
PYTHONPATH= .venv/bin/python -m vda5050_master.main

# terminal 2
PYTHONPATH= .venv/bin/python -m vda5050_client.main
```

## What's implemented

- **V0** (core happy path): client startup, order assignment,
  node/edge traversal, state publishing, completion detection.
- **V1** (reliability): order rejection, disconnect handling
  (`CONNECTIONBROKEN` / graceful `OFFLINE` / broker-down), `cancelOrder`,
  action blocking (`SOFT`/`HARD`), state heartbeat.
- **V2** (full spec correctness — order update/stitching,
  `newBaseRequest`, full Figure 8/17 nuance): not yet implemented.

See `plan.md` for the full checklist and `docs/design_doc.md` §11 for the
V0/V1/V2 scope breakdown.
