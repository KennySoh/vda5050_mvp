from vda5050_common.models import Action, ActionStatus, BlockingType

from vda5050_client.actions import ActionRunner


def make_action(action_id="action-1", blocking_type=BlockingType.NONE):
    return Action(actionType="pick", actionId=action_id, blockingType=blocking_type)


def test_action_lifecycle_waiting_running_finished():
    runner = ActionRunner()
    action = make_action()
    runner.start_action(action)
    assert runner.action_states()[0].actionStatus == ActionStatus.WAITING

    runner.tick_actions()
    assert runner.action_states()[0].actionStatus == ActionStatus.RUNNING

    runner.tick_actions()
    assert runner.action_states()[0].actionStatus == ActionStatus.FINISHED


def test_none_blocking_type_does_not_block_driving():
    runner = ActionRunner()
    runner.start_action(make_action(blocking_type=BlockingType.NONE))
    assert runner.is_driving_blocked() is False


def test_soft_and_hard_blocking_types_block_driving():
    runner = ActionRunner()
    runner.start_action(make_action(action_id="soft", blocking_type=BlockingType.SOFT))
    assert runner.is_driving_blocked() is True

    runner = ActionRunner()
    runner.start_action(make_action(action_id="hard", blocking_type=BlockingType.HARD))
    assert runner.is_driving_blocked() is True


def test_blocking_clears_once_action_finishes():
    runner = ActionRunner()
    runner.start_action(make_action(blocking_type=BlockingType.HARD))
    assert runner.is_driving_blocked() is True

    runner.tick_actions()  # WAITING -> RUNNING
    assert runner.is_driving_blocked() is True

    runner.tick_actions()  # RUNNING -> FINISHED
    assert runner.is_driving_blocked() is False


def test_fail_all_running_marks_pending_actions_failed():
    runner = ActionRunner()
    runner.start_action(make_action(action_id="a"))
    runner.start_action(make_action(action_id="b"))
    runner.tick_actions()  # both WAITING -> RUNNING

    runner.fail_all_running()

    statuses = {state.actionId: state.actionStatus for state in runner.action_states()}
    assert statuses == {"a": ActionStatus.FAILED, "b": ActionStatus.FAILED}
    assert runner.is_driving_blocked() is False
