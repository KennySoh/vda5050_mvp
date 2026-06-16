from __future__ import annotations

from typing import Dict, List

from vda5050_common.models import Action, ActionState, ActionStatus, BlockingType


class ActionRunner:
    def __init__(self) -> None:
        self._states: Dict[str, ActionState] = {}
        self._blocking_types: Dict[str, BlockingType] = {}
        self._pending: List[str] = []

    def start_action(self, action: Action) -> None:
        self._states[action.actionId] = ActionState(
            actionId=action.actionId,
            actionType=action.actionType,
            actionStatus=ActionStatus.WAITING,
        )
        self._blocking_types[action.actionId] = action.blockingType
        self._pending.append(action.actionId)

    def tick_actions(self) -> None:
        still_pending = []
        for action_id in self._pending:
            state = self._states[action_id]
            if state.actionStatus == ActionStatus.WAITING:
                state.actionStatus = ActionStatus.RUNNING
                still_pending.append(action_id)
            elif state.actionStatus == ActionStatus.RUNNING:
                state.actionStatus = ActionStatus.FINISHED
        self._pending = still_pending

    def is_driving_blocked(self) -> bool:
        return any(
            self._blocking_types[action_id] in (BlockingType.SOFT, BlockingType.HARD)
            for action_id in self._pending
        )

    def fail_all_running(self) -> None:
        for action_id in self._pending:
            self._states[action_id].actionStatus = ActionStatus.FAILED
        self._pending = []

    def action_states(self) -> List[ActionState]:
        return list(self._states.values())
