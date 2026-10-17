from functools import partial
from api.od import ODAPI
from examples.ftg_pm_pt.helpers.composite_activity import get_target_outgoing
from transformation.cloner import clone_od


def precondition_previous_step_completed(od: ODAPI, step_state: str):
    # Check whether the preceding step was completed for the same order
    step_state = od.get(step_state)

    step = od.get_target(od.get_outgoing(step_state, "stateOfStep")[0])

    previous_link = od.get_incoming(step, "nextStep")

    # first step doesn't have a previous step
    if not previous_link:
        return True

    previous_step = od.get_source(previous_link[0])

    previous_step_state = od.get_source(od.get_incoming(previous_step, "stateOfStep")[0])

    return od.has_slot(previous_step_state, "finishedAt") and od.get_slot_value(previous_step_state, "finishedAt") < get_time(od)



def precondition_tools_free(od: ODAPI, step: str):
    # Check whether all tools needed in this step are ava ilable
    step = od.get(step)
    required_tools = [od.get_target(link) for link in od.get_outgoing(step, "hasTool")]

    for tool in required_tools:
        tool_state = od.get_source(od.get_incoming(tool, "stateOfTool")[0])
        if od.get_slot_value(tool_state, "inUse"):
            return False
    return True


def precondition_cooks_not_moved(od: ODAPI, step: str):
    # Check whether none of the associated cooks has already performed an action in this time-step
    step = od.get(step)
    cooks = [od.get_target(link) for link in od.get_outgoing(step, "hasCook")]

    time = get_time(od)
    for cook in cooks:
        cook_state = od.get_source(od.get_incoming(cook, "stateOfCook")[0])
        if od.get_slot_value(cook_state, "lastMovedAt") == time:
            return False
    return True

def precondition_cooks_free(od: ODAPI, step: str):
    # Check whether all associated cooks are available (not busy and didn't already act)
    step = od.get(step)
    cooks = [od.get_target(link) for link in od.get_outgoing(step, "hasCook")]

    for cook in cooks:
        cook_state = od.get_source(od.get_incoming(cook, "stateOfCook")[0])
        if od.get_slot_value(cook_state, "busy"):
            return False

    return precondition_cooks_not_moved(od, step)

def precondition_can_start_step(od: ODAPI, step_state: str):
    # Check whether all conditions to start the step are met
    step_state = od.get(step_state)
    step = od.get_target(od.get_outgoing(step_state, "stateOfStep")[0])

    # step shouldn't be already started
    if od.has_slot(step_state, "startedAt"):
        return False

    if not precondition_previous_step_completed(od, step_state):
        return False

    if not precondition_tools_free(od, step):
        return False

    if not precondition_cooks_free(od, step):
        return False

    return True

def precondition_can_finish_step(od: ODAPI, step_state: str):
    # Check whether all conditions to finish the step are met
    step_state = od.get(step_state)

    if not od.has_slot(step_state, "startedAt"):
        return False

    if od.has_slot(step_state, "finishedAt"):
        return False

    step = od.get_target(od.get_outgoing(step_state, "stateOfStep")[0])

    # cook is busy with another thing
    if not precondition_cooks_not_moved(od, od.get_name(step)):
        return False

    action = od.get_target(od.get_outgoing(step, "hasAction")[0])

    # if the action is not attended and there are no free cooks, action can't complete
    if not od.get_slot_value(action, "attended"):
        if not precondition_cooks_free(od, od.get_name(step)):
            return False

    duration = od.get_slot_value(step, "duration")

    return (get_time(od) - od.get_slot_value(step_state, "startedAt") >= max(1, duration))


def precondition_can_serve_order(od: ODAPI, order: str):
    # Check that all steps of the order were completed before the current time
    order = od.get(order)
    time = get_time(od)

    step_states = [od.get_source(link) for link in od.get_incoming(order, "stateOfOrder")]

    for state in step_states:
        if not od.has_slot(state, "finishedAt"):
            return False

        if od.get_slot_value(state, "finishedAt") >= time:
            return False

    return True

def precondition_can_take_order(od: ODAPI):
    # Check whether an order can be accepted in the current timestep (no other order was accepted already)
    time = get_time(od)

    for _, order in od.get_all_instances("Order"):
        if od.get_slot_value(order, "arrivedAt") == time:
            return False

    return True

def action_take_order(od: ODAPI, dish: str):
    # Create a new order for the dish and all other needed instances
    dish = od.get(dish)
    time = get_time(od)

    number = len(od.get_all_instances("Order")) + 1
    order = od.create_object(f"Order{number}", "Order")

    od.set_slot_value(order, "arrivedAt", time)
    od.create_link(None, "OrderDish", order, dish)

    steps = [od.get_target(link) for link in od.get_outgoing(dish, "hasStep")]

    for step in steps:
        step_state = od.create_object(f"Order{number}_{od.get_name(step)}State","StepState")

        od.create_link(None, "stateOfStep", step_state, step)
        od.create_link(None, "stateOfOrder", step_state, order)

    return [f"Order {number} for {od.get_slot_value(dish, 'dishName')} accepted"]

def action_start_step(od: ODAPI, step_state: str):
    # Claim all resources and remember the start time
    step_state = od.get(step_state)
    time = get_time(od)

    od.set_slot_value(step_state, "startedAt", time)
    step = od.get_target(od.get_outgoing(step_state, "stateOfStep")[0])

    required_tools = [od.get_target(link) for link in od.get_outgoing(step, "hasTool")]

    for tool in required_tools:
        tool_state = od.get_source(od.get_incoming(tool, "stateOfTool")[0])
        od.set_slot_value(tool_state, "inUse", True)

    action = od.get_target(od.get_outgoing(step, "hasAction")[0])
    attended = od.get_slot_value(action, "attended")

    required_cooks = [od.get_target(link) for link in od.get_outgoing(step, "hasCook")]

    for cook in required_cooks:
        cook_state = od.get_source(od.get_incoming(cook, "stateOfCook")[0])
        od.set_slot_value(cook_state, "busy", attended)
        od.set_slot_value(cook_state, "lastMovedAt", time)

    return [f"Step {od.get_name(step)} started at time {time}"]


def action_finish_step(od: ODAPI, step_state: str):
    # Release all resources and remember the finish time
    step_state = od.get(step_state)
    time = get_time(od)

    od.set_slot_value(step_state, "finishedAt", time)
    step = od.get_target(od.get_outgoing(step_state, "stateOfStep")[0])

    required_tools = [od.get_target(link) for link in od.get_outgoing(step, "hasTool")]

    for tool in required_tools:
        tool_state = od.get_source(od.get_incoming(tool, "stateOfTool")[0])
        od.set_slot_value(tool_state, "inUse", False)

    required_cooks = [od.get_target(link) for link in od.get_outgoing(step, "hasCook")]

    for cook in required_cooks:
        cook_state = od.get_source(od.get_incoming(cook, "stateOfCook")[0])
        od.set_slot_value(cook_state, "busy", False)
        od.set_slot_value(cook_state, "lastMovedAt", time)

    return [f"Step {od.get_name(step)} finished at time {time}"]


def action_serve_order(od: ODAPI, order: str):
    # Remove the order and all associated elements from the model and increase the count
    order = od.get(order)

    dish = od.get_target( od.get_outgoing(order, "OrderDish")[0])

    dish_state = od.get_source(od.get_incoming(dish, "stateOfDish")[0])

    od.set_slot_value(dish_state,"served", od.get_slot_value(dish_state, "served") + 1)

    step_states = [ od.get_source(link) for link in od.get_incoming(order, "stateOfOrder")]

    for step_state in step_states:
        od.delete(step_state)

    od.delete(order)

    return [f"Order for {od.get_slot_value(dish, 'dishName')} served"]


def action_advance_time(od: ODAPI):
    #  Advance the clock - copied from demo
    _, clock = od.get_all_instances("Clock")[0]
    od.set_slot_value(clock, "time", get_time(od) + 1)
    return [f"Time updated to {get_time(od)}"]

def get_time(od: ODAPI):
    _, clock = od.get_all_instances("Clock")[0]
    return od.get_slot_value(clock, "time")

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
