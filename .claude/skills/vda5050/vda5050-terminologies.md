# VDA5050 v2.1.0 — Terminology actually used in the document

Every term below appears verbatim in `VDA5050-V2.1.0-2025-01-1-4.pdf`
(field name, JSON object name, topic name, enum value, or a named concept
used in the prose/glossary). This is a **closed list** — if a word you're
about to use isn't here, it's not spec vocabulary, it's an implementation
choice (see §8 for examples from `docs/design_doc.md` that are *not* spec terms).

---

## 1. Topic names (literal MQTT topic strings used by the protocol)

```
order
instantActions
state
visualization
connection
factsheet
```

## 2. Top-level message/object names

```
header            (not a JSON object itself, but referred to as "the header")
Order             order.schema
InstantActions    instantActions.schema
State             state.schema
Connection        connection.schema
Factsheet         factsheet.schema
node
edge
action
trajectory
controlPoint
corridor
nodePosition
actionParameter
map
nodeState
edgeState
agvPosition
velocity
load
boundingBoxReference
loadDimensions
actionState
batteryState
error
errorReference
info
infoReference
safetyState
typeSpecification
physicalParameters
protocolLimits
protocolFeatures
agvGeometry
loadSpecification
vehicleConfig
wheelDefinition
envelope2d
envelope3d
loadSet
optionalParameter
agvAction
versionInfo
maxStringLens
maxArrayLens
timing
network
```

## 3. Field names (camelCase, exactly as in the spec's tables)

**Header (every message starts with this):**
```
headerId  timestamp  version  manufacturer  serialNumber
```

**Order:**
```
orderId  orderUpdateId  zoneSetId  nodes  edges
```

**node:**
```
nodeId  sequenceId  nodeDescription  released  nodePosition  actions
```

**nodePosition:**
```
x  y  theta  allowedDeviationXY  allowedDeviationTheta  mapId  mapDescription
```

**edge:**
```
edgeId  sequenceId  edgeDescription  released  startNodeId  endNodeId
maxSpeed  maxHeight  minHeight  orientation  orientationType  direction
rotationAllowed  maxRotationSpeed  trajectory  length  corridor  action
```

**trajectory:**
```
degree  knotVector  controlPoints
```

**controlPoint:**
```
x  y  weight
```

**corridor:**
```
leftWidth  rightWidth  corridorRefPoint
```

**action:**
```
actionType  actionId  actionDescription  blockingType  actionParameters
```

**actionParameter:**
```
key  value
```

**instantActions:**
```
actions
```

**state (top level):**
```
maps  orderId  orderUpdateId  zoneSetId  lastNodeId  lastNodeSequenceId
nodeStates  edgeStates  agvPosition  velocity  loads  driving  paused
newBaseRequest  distanceSinceLastNode  actionStates  batteryState
operatingMode  errors  information  safetyState
```

**map:**
```
mapId  mapVersion  mapDescription  mapStatus
```

**nodeState:** (same shape as `node`)
```
nodeId  sequenceId  nodeDescription  released  nodePosition
```

**edgeState:**
```
edgeId  sequenceId  edgeDescription  released  trajectory
```

**agvPosition:**
```
positionInitialized  localizationScore  deviationRange  x  y  theta
mapId  mapDescription
```

**velocity:**
```
vx  vy  omega
```

**load:**
```
loadId  loadType  loadPosition  boundingBoxReference  loadDimensions  weight
```

**boundingBoxReference:**
```
x  y  z  theta
```

**loadDimensions:**
```
length  width  height
```

**actionState:**
```
actionId  actionType  actionDescription  actionStatus  resultDescription
```

**batteryState:**
```
batteryCharge  batteryVoltage  batteryHealth  charging  reach
```

**error:**
```
errorType  errorReferences  errorDescription  errorHint  errorLevel
```

**errorReference / infoReference:**
```
referenceKey  referenceValue
```

**info:**
```
infoType  infoReferences  infoDescription  infoLevel
```

**safetyState:**
```
eStop  fieldViolation
```

**connection:**
```
connectionState
```

**factsheet (top level):**
```
typeSpecification  physicalParameters  protocolLimits  protocolFeatures
agvGeometry  loadSpecification  vehicleConfig
```

**typeSpecification:**
```
seriesName  seriesDescription  agvKinematic  agvClass  maxLoadMass
localizationTypes  navigationTypes
```

**physicalParameters:**
```
speedMin  speedMax  angularSpeedMin  angularSpeedMax  accelerationMax
decelerationMax  heightMin  heightMax  width  length
```

**protocolLimits:**
```
maxStringLens  msgLen  topicSerialLen  topicElemLen  idLen  idNumericalOnly
enumLen  loadIdLen  maxArrayLens  timing  minOrderInterval  minStateInterval
defaultStateInterval  visualizationInterval
```

(`maxArrayLens` sub-fields:)
```
order.nodes  order.edges  node.actions  edge.actions
actions.actionsParameters  instantActions  trajectory.knotVector
trajectory.controlPoints  state.nodeStates  state.edgeStates  state.loads
state.actionStates  state.errors  state.information
error.errorReferences  information.infoReferences
```

**protocolFeatures:**
```
optionalParameters  parameter  support  description  agvActions  actionType
actionDescription  actionScopes  actionParameters  key  valueDataType
isOptional  resultDescription  blockingTypes
```

**agvGeometry:**
```
wheelDefinitions  type  isActiveDriven  isActiveSteered  position  diameter
width  centerDisplacement  constraints  envelopes2d  set  polygonPoints
description  envelopes3d  format  data  url
```

**loadSpecification:**
```
loadPositions  loadSets  setName  loadType  boundingBoxReference
loadDimensions  maxWeight  minLoadhandlingHeight  maxLoadhandlingHeight
minLoadhandlingDepth  maxLoadhandlingDepth  minLoadhandlingTilt
maxLoadhandlingTilt  agvSpeedLimit  agvAccelerationLimit
agvDecelerationLimit  pickTime  dropTime  description
```

**vehicleConfig:**
```
versions  key  value  network  dnsServers  ntpServers  localIpAddress
netmask  defaultGateway
```

## 4. Predefined action names (`actionType` values)

```
startPause  stopPause  startCharging  stopCharging  initPosition
enableMap  downloadMap  deleteMap  stateRequest  logReport  pick  drop
detectObject  finePositioning  waitForTrigger  cancelOrder  factsheetRequest
```

## 5. Enum values (UPPERCASE, exactly as spelled in the spec)

```
actionStatus      WAITING INITIALIZING RUNNING PAUSED FINISHED FAILED
blockingType      NONE SOFT HARD
operatingMode     AUTOMATIC SEMIAUTOMATIC MANUAL SERVICE TEACHIN
orientationType   GLOBAL TANGENTIAL
corridorRefPoint  KINEMATICCENTER CONTOUR
mapStatus         ENABLED DISABLED
connectionState   ONLINE OFFLINE CONNECTIONBROKEN
errorLevel        WARNING FATAL
eStop             AUTOACK MANUAL REMOTE NONE
wheelDefinition.type   DRIVE CASTER FIXED MECANUM
agvKinematic      DIFF OMNI THREEWHEEL
agvClass          FORKLIFT CONVEYOR TUGGER CARRIER
infoLevel         DEBUG INFO
actionScopes      INSTANT NODE EDGE
support           SUPPORTED REQUIRED
valueDataType     BOOL NUMBER INTEGER FLOAT STRING OBJECT ARRAY
```

Example values given for free-text/array fields (spec explicitly lists
these as *examples*, not closed enums):
```
localizationTypes   NATURAL REFLECTOR RFID DMC SPOT GRID
navigationTypes     PHYSICAL_LINE_GUIDED VIRTUAL_LINE_GUIDED AUTONOMOUS
```

## 6. Error/warning identifiers named in prose

```
validationError
orderError
orderUpdateError
noOrderToCancel
```

## 7. Named concepts used in the prose/glossary (not JSON fields, but spec
vocabulary — these are the words the document itself uses to talk about
its own mechanics)

```
driverless transport system (DTS)
master control
automated guided vehicle (AGV)
freely navigating vehicle
free navigation AGV
guided vehicles (physical or virtual)
autonomous vehicle
swarm intelligence
central map
base
horizon
decision point
stitching
order
order update
sub-order
plug and play
intralogistics
MQTT
MQTT broker
topic
JSON
NURBS
Layout Interchange Format (LIF)
map server
pull operation (for map transfer)
last will
heartbeat
retained (flag)
Quality of Service (QoS)
Best Effort
At Least Once
semantic versioning
major version / minor version / patch version
traffic control
deadlock
energy management
buffer route / buffer station
waiting position
charging spot
charging lane
kinematic center
contour
pivot point
envelope
footprint
line-guided vehicle
wire-guided vehicle
underrun tractor
fork lift AGV
operator
integrator
```

## 8. NOT spec vocabulary — current implementation plan

An earlier `/home/kenny/rmf2.0/plan.md` (ROS 2 / `vda5050_interfaces.msg`)
and two earlier plain-MQTT drafts have all been **deleted and
superseded** by the single, self-sufficient `vda5050_mvp/docs/design_doc.md`. Its
decisions: no ROS, plain `paho-mqtt`, pydantic v2 models using verbatim
camelCase spec field names (no alias layer), plain `Optional[X] = None`
for optionals, corrected QoS table (`order`/`instantActions`/`state`/
`factsheet`/`visualization` = QoS 0, `connection` = QoS 1 — the deleted
ROS plan had this backwards). Module layout reconciles a
community/ChatGPT-authored draft the user liked: files are named after
the **topic they own** where that's the module's whole job
(`orders.py`↔`order`, `state.py`↔`state`), and explicitly flag the files
that have no spec equivalent at all (`fleet.py`, `master.py`,
`vehicle.py`, `mqtt.py`, `main.py`). Sequence diagrams are one PlantUML
file per demo-flow scenario under `vda5050_mvp/docs/diagrams/`, each with a
locally-rendered `.png` next to it, rather than embedded in the plan
document — plus a V0/V1/V2 implementation priority.

File names that **are** literal topic names (it's the *topic*, not the
filename convention itself, that's the spec term):

```
orders.py    (master + client, one per side — topic "order"; master's
              orders.py also builds InstantActions, since master only
              ever constructs outbound messages, never receives them)
state.py      (client — topic "state")
```

`connection`/`factsheet` (client) are handled inside `mqtt.py` at this
size rather than getting their own files — the logic is a few lines with
no decisions in it (publish `ONLINE`/`OFFLINE`/retained `factsheet`).

File/class/function names below have **no** spec equivalent at all — none
of them appear in the PDF:

```
# vda5050_master/
fleet.py    Fleet  Agv  get_or_create()  record_state()  record_connection()
            record_factsheet()  clear_current_order()  mark_unreachable()
            (per-AGV bookkeeping — the spec never describes how a master
            internally tracks multiple AGVs, only the wire messages)
master.py   assign_order()  cancel_order()  on_state()  on_connection()
            on_factsheet()  (the decision brain — no spec concept of this
            at all, only the messages it reacts to)
mqtt.py (master)   (transport glue only)
main.py (master)

# vda5050_client/
vehicle.py  tick()  move_towards_next_node()  check_node_reached()
            (the one module a real robot driver replaces — deliberately
            not spec-named, since the spec defines the AGV's interface,
            never its internals/kinematics)
mqtt.py (client)   (transport + connection/factsheet glue)
main.py (client)

# functions inside the topic-named files above (still invented, even
# though the file they live in is topic-named)
build_order()  build_order_update()  build_instant_actions()  (orders.py, master)
accept_or_reject()  apply_order()  mark_node_reached()  cancel_order()
is_order_complete()  next_node()                              (orders.py, client)
start_action()  tick_actions()  is_driving_blocked()  fail_all_running()  (actions.py)
mark_dirty()  build_state()  should_publish()  clear_dirty()  (state.py)

# shared (vda5050_common/) — module names only, the *types* inside are spec terms
models.py
topics.py
mqtt.py
time.py
```

The `EventName` enum and every "Events:" list in `vda5050_mvp/docs/design_doc.md`
§9/§10 (`OrderAccepted`, `NodeReached`, `StateDirty`, …) are also our own
logging vocabulary, not spec terms.

If you want code identifiers to read as "obviously VDA5050," prefer
naming a *file* after a topic when the module's whole job is that topic,
and reserve generic agent/verb names (`Fleet`, `master.py`, `vehicle.py`,
`main`) only for the parts that genuinely have no spec equivalent — so
it's visually obvious in code which names are "the spec" and which are
"our architecture."

## 9. A third category — borrowed from `rmf2_device_manager`, neither spec nor ours

`vda5050_mvp/docs/design_doc.md` §13 documents three names that are deliberately
**not** in either bucket above:

```
AssignmentDecision   ACCEPTED  QUEUED  REJECTED_PREFLIGHT  REJECTED_POSTFLIGHT
OrderPhase            NO_ORDER  ACCEPTED  RUNNING  COMPLETED  FAILED
MasterConnectionState STARTING  READY  DEGRADED  SHUTTING_DOWN
```

These aren't in the VDA5050 PDF (§8's rule still holds: if it's not in
the closed lists above, it's not spec vocabulary) — but they're also not
something *we* invented for this project. They're copied on purpose from
`rmf2_device_manager`'s VDA5050 Master Device Controller design (local
reference copies: `vda5050_mvp/docs/references/messages/msg/
{AssignmentResult,OrderStatus,MasterConnection}.msg`), so this
prototype's `master.py` can port forward without a rename. One
intentional deviation from the reference: their `OrderStatus.msg` prefixes
each phase constant (`PHASE_NO_ORDER`, `PHASE_ACCEPTED`, …) because flat
ROS `uint8` constants need the prefix to avoid clashing; our `OrderPhase`
enum doesn't need it (`OrderPhase.NO_ORDER` already disambiguates via the
enum class), so the prefix is dropped — same values, shorter names.

If a future change touches `master.py`'s order-lifecycle or
connection-health logic, check `docs/design_doc.md` §13 and the referenced `.msg`
files before inventing a fourth name for the same concept.
