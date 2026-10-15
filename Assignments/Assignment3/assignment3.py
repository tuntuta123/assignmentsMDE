from functools import partial
from api.od import ODAPI
from transformation.cloner import clone_od


def precondition_previous_step_completed(od: ODAPI, step_state: str):
    # TODO: Check whether the preceding step was completed for the same order
    raise NotImplementedError()


def precondition_tools_free(od: ODAPI, step: str):
    # TODO: Check whether all tools needed in this step are available
    raise NotImplementedError()


def precondition_cooks_not_moved(od: ODAPI, step: str):
    # TODO: Check whether none of the associated cooks has already performed an action in this time-step
    raise NotImplementedError()


def precondition_cooks_free(od: ODAPI, step: str):
    # TODO: Check whether all associated cooks are available (not busy and didn't already act)
    raise NotImplementedError()


def precondition_can_start_step(od: ODAPI, step_state: str):
    # TODO: Check whether all conditions to start the step are met
    raise NotImplementedError()


def precondition_can_finish_step(od: ODAPI, step_state: str):
    # TODO: Check whether all conditions to finish the step are met
    raise NotImplementedError()


def precondition_can_serve_order(od: ODAPI, order: str):
    # TODO: Check that all steps of the order were completed before the current time
    raise NotImplementedError()


def precondition_can_take_order(od: ODAPI):
    # TODO: Check whether an order can be accepted in the current timestep (no other order was accepted already)
    raise NotImplementedError()


def action_take_order(od: ODAPI, dish: str):
    # TODO: Create a new order for the dish and all other needed instances
    raise NotImplementedError()


def action_start_step(od: ODAPI, step_state: str):
    # TODO: Claim all resources and remember the start time
    raise NotImplementedError()


def action_finish_step(od: ODAPI, step_state: str):
    # TODO: Release all resources and remember the finish time
    raise NotImplementedError()


def action_serve_order(od: ODAPI, order: str):
    # TODO: Remove the order and all associated elements from the model and increase the count
    raise NotImplementedError()


def action_advance_time(od: ODAPI):
    # TODO: Advance the clock
    raise NotImplementedError()


def get_actions(od: ODAPI):
    """
        Retrieve the actions that are possible in the current state
    """
    # Dictionary mapping "Action text" to the (partial) function that is executed
    actions = {}

    # TODO: Determine the currently possible actions and add them to the actions dictionary

    return make_actions_pure(actions.items(), od)


def make_actions_pure(actions, od):
    # Copy model before modifying it
    def exec_pure(action_to_exec, original_od):
        cloned_rt_m = clone_od(original_od.state, original_od.m, original_od.mm)
        new_od = ODAPI(original_od.state, cloned_rt_m, original_od.mm)
        msgs = action_to_exec(new_od)
        return new_od, msgs

    for descr, action in actions:
        yield descr, partial(exec_pure, action, od)


def termination_condition(od: ODAPI):
    # TODO: implement the termination conditions
    #  Returning None means no termination condition is satisfied
    #  Otherwise, return a string with the reason for termination

    return None
