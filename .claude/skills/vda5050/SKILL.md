---
name: vda5050
description: Reference for the VDA 5050 v2.1.0 protocol (interface between AGVs/AMRs and a master control/fleet manager over MQTT+JSON). Use when working with VDA5050 orders, instantActions, state, visualization, connection, or factsheet topics, or with terms like AGV, master control, base/horizon, orderUpdateId, nodeState/edgeState/actionState, blockingType, corridor, or VDA5050 JSON schemas — e.g. implementing/debugging an AGV driver, a fleet adapter, or RMF2.0 integration against VDA5050-speaking robots.
---

# VDA 5050 v2.1.0

VDA 5050 is the VDA/VDMA recommendation defining the MQTT+JSON communication
interface between a **master control** (fleet manager) and **AGVs**
(automated guided vehicles) in a driverless transport system (DTS). It lets
AGVs from different manufacturers be controlled by one master control using a
uniform order/state protocol.

Full terminology, JSON field tables, state machines, and worked examples are
in `vda5050-v2.1.0-overview.md` in this skill folder — read it before
implementing or debugging anything VDA5050-related. The source spec PDF is
`VDA5050-V2.1.0-2025-01-1-4.pdf`, also in this skill folder.

## When to reach for the overview file

- Implementing or reviewing an AGV-side or master-control-side VDA5050 client.
- Debugging order rejection, order-update ("stitching"), or cancelOrder flows.
- Working with `nodeStates`/`edgeStates`/`actionStates` in the `state` topic.
- Adding/parsing a predefined action (`pick`, `drop`, `initPosition`,
  `startPause`, `cancelOrder`, map actions, etc.) or its `actionStatus`
  lifecycle.
- Mapping coordinate systems, corridors, trajectories (NURBS), or maps between
  master control and an AGV.
- Reading or generating an AGV `factsheet`.
- Translating any VDA5050 jargon (base, horizon, decision point, sequenceId,
  blockingType, free-navigation AGV vs. guided vehicle, etc.) into something
  concrete for this codebase.

## Quick facts

- Transport: MQTT 3.1.1+, JSON payloads, QoS 0 for `order`/`instantActions`/
  `state`/`factsheet`/`visualization`, QoS 1 for `connection`.
- Suggested topic shape: `interfaceName/majorVersion/manufacturer/serialNumber/topic`
  (e.g. `uagv/v2/KIT/0001/order`).
- Six topics: `order`, `instantActions` (MC→AGV), `state`, `visualization`
  (optional), `connection` (AGV/broker→MC), `factsheet` (AGV→MC).
- An order is a graph of `nodes`/`edges`; the **base** (released) is binding,
  the **horizon** (unreleased) can still change; updates are tracked via
  `orderId` + `orderUpdateId`, with `sequenceId` for ordering/loop support.

When in doubt about exact field names, types, or enum values, grep the
overview file rather than guessing — VDA5050 keywords are case-sensitive
camelCase and enums are UPPERCASE.
