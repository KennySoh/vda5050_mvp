from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel


class Header(BaseModel):
    headerId: int
    timestamp: str
    version: str
    manufacturer: str
    serialNumber: str


class BlockingType(str, Enum):
    NONE = "NONE"
    SOFT = "SOFT"
    HARD = "HARD"


class ActionStatus(str, Enum):
    WAITING = "WAITING"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class OperatingMode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    SEMIAUTOMATIC = "SEMIAUTOMATIC"
    MANUAL = "MANUAL"
    SERVICE = "SERVICE"
    TEACHIN = "TEACHIN"


class ErrorLevel(str, Enum):
    WARNING = "WARNING"
    FATAL = "FATAL"


class InfoLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"


class EStop(str, Enum):
    AUTOACK = "AUTOACK"
    MANUAL = "MANUAL"
    REMOTE = "REMOTE"
    NONE = "NONE"


class ConnectionState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CONNECTIONBROKEN = "CONNECTIONBROKEN"


class AgvKinematic(str, Enum):
    DIFF = "DIFF"
    OMNI = "OMNI"
    THREEWHEEL = "THREEWHEEL"


class AgvClass(str, Enum):
    FORKLIFT = "FORKLIFT"
    CONVEYOR = "CONVEYOR"
    TUGGER = "TUGGER"
    CARRIER = "CARRIER"


class ActionParameter(BaseModel):
    key: str
    value: Union[bool, float, int, str, list, dict]


class Action(BaseModel):
    actionType: str
    actionId: str
    actionDescription: Optional[str] = None
    blockingType: BlockingType
    actionParameters: Optional[List[ActionParameter]] = None


class NodePosition(BaseModel):
    x: float
    y: float
    theta: Optional[float] = None
    allowedDeviationXY: Optional[float] = None
    allowedDeviationTheta: Optional[float] = None
    mapId: str
    mapDescription: Optional[str] = None


class Node(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: Optional[str] = None
    released: bool
    nodePosition: Optional[NodePosition] = None
    actions: List[Action] = []


class Edge(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: Optional[str] = None
    released: bool
    startNodeId: str
    endNodeId: str
    maxSpeed: Optional[float] = None
    maxHeight: Optional[float] = None
    minHeight: Optional[float] = None
    orientation: Optional[float] = None
    orientationType: Optional[str] = None
    direction: Optional[str] = None
    rotationAllowed: Optional[bool] = None
    maxRotationSpeed: Optional[float] = None
    length: Optional[float] = None
    actions: List[Action] = []


class Order(Header):
    orderId: str
    orderUpdateId: int
    nodes: List[Node]
    edges: List[Edge]


class InstantActions(Header):
    actions: List[Action]


class NodeState(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: Optional[str] = None
    released: bool
    nodePosition: Optional[NodePosition] = None


class EdgeState(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: Optional[str] = None
    released: bool


class ActionState(BaseModel):
    actionId: str
    actionType: Optional[str] = None
    actionDescription: Optional[str] = None
    actionStatus: ActionStatus
    resultDescription: Optional[str] = None


class BatteryState(BaseModel):
    batteryCharge: float
    batteryVoltage: Optional[float] = None
    batteryHealth: Optional[int] = None
    charging: bool
    reach: Optional[int] = None


class ErrorReference(BaseModel):
    referenceKey: str
    referenceValue: str


class Error(BaseModel):
    errorType: str
    errorReferences: List[ErrorReference] = []
    errorDescription: Optional[str] = None
    errorHint: Optional[str] = None
    errorLevel: ErrorLevel


class InfoReference(BaseModel):
    referenceKey: str
    referenceValue: str


class Info(BaseModel):
    infoType: str
    infoReferences: List[InfoReference] = []
    infoDescription: Optional[str] = None
    infoLevel: InfoLevel


class SafetyState(BaseModel):
    eStop: EStop
    fieldViolation: bool


class State(Header):
    orderId: str = ""
    orderUpdateId: int = 0
    lastNodeId: str = ""
    lastNodeSequenceId: int = 0
    nodeStates: List[NodeState] = []
    edgeStates: List[EdgeState] = []
    driving: bool = False
    paused: Optional[bool] = None
    newBaseRequest: Optional[bool] = None
    distanceSinceLastNode: Optional[float] = None
    actionStates: List[ActionState] = []
    batteryState: BatteryState
    operatingMode: OperatingMode
    errors: List[Error] = []
    information: Optional[List[Info]] = None
    safetyState: SafetyState


class Connection(Header):
    connectionState: ConnectionState


class TypeSpecification(BaseModel):
    seriesName: str
    seriesDescription: Optional[str] = None
    agvKinematic: AgvKinematic
    agvClass: AgvClass
    maxLoadMass: float
    localizationTypes: List[str] = []
    navigationTypes: List[str] = []


class Factsheet(Header):
    typeSpecification: TypeSpecification
