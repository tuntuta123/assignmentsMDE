import functools
import os.path
from collections import Counter

from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od.parser import parse_od
from state.devstate import DevState
from transformation.matcher import match_od
from transformation.ramify import ramify
from transformation.rule import RuleMatcherRewriter, PriorityActionGenerator
from util.loader import parse_and_check, load_rules
from util.simulator import InteractiveDecisionMaker

from models import mm_dish, m_dish, rt_mm_dish, rt_m_dish
from simulator import KitchenSimulator

# Rules the user chooses from, grouped by priority (high -> low).
ACTION_RULES = [
    # TODO: add your rules, grouped by priority (= list of lists)
]

# Rules that keep the runtime state consistent.
# They are not offered as choices: after every action they are applied until none of them matches anymore.
BOOKKEEPING_RULES = [
    # TODO: add bookkeeping rules, all have the same priority
]


class TerminationCondition:
    def __init__(self, state, rt_mm):
        self.state = state
        self.rt_mm_ramified = ramify(state, rt_mm)

        # these patterns were largely based on the termination conditions in assignment 3
        patterns_cs = {
            # add termination condition patterns, key = reason, value = pattern

            # terminate if 3 orders have been served across all dishes, so use the clock as a sort of anchor to check all the dishes
            # so for every dish get the served attribute and terminate if the sum is >= 3
            "Three orders have been served. ": """            
            clock:RAM_Clock {
            condition = `sum([get_slot_value(dish_state, "served") for _, dish_state in get_all_instances("DishState")]) >= 3`;
            }
            """,

            # use the clock as an anchor again, here we want to return True if we need to terminate,
            # so the result is inverted compared to assignment 3
            "One order has taken double its cooktime. ": """
            clock: RAM_Clock{
                condition = ```
                terminate = False
                time = get_slot_value(this, "time")
                for _, order in get_all_instances("Order"):
                    dish = get_target(get_outgoing(order, "OrderDish")[0])
                    waited = time - get_slot_value(order, "arrivedAt")
                    if waited >= 2 * get_slot_value(dish, "cooktime"):
                        terminate = True
                
                terminate
                ```;
            }
            """
        }

        self.patterns = {cause: parse_od(state, pattern_cs, self.rt_mm_ramified)
                         for cause, pattern_cs in patterns_cs.items()}

    def __call__(self, od):
        for cause, pattern in self.patterns.items():
            for match in match_od(self.state, od.m, od.mm, pattern, self.rt_mm_ramified):
                # stop after the first match (no need to look for more matches):
                return cause.format(**match)


class BookkeepingActionGenerator:
    def __init__(self, action_generator, matcher_rewriter, bookkeeping_rules):
        self.action_generator = action_generator
        self.matcher_rewriter = matcher_rewriter
        self.bookkeeping_rules = bookkeeping_rules

    def __call__(self, od: ODAPI):
        for descr, action in self.action_generator(od):
            yield descr, functools.partial(self.execute, action)

    def execute(self, action):
        od, msgs = action()
        od, applied = self.settle(od)
        if applied:
            msgs.append("bookkeeping: " + ", ".join(f"{name} x{count}" for name, count in applied.items()))
        return od, msgs

    def settle(self, od: ODAPI):
        # The model was already cloned by the chosen action, so it can be rewritten in place
        applied = Counter()
        changed = True
        while changed:
            changed = False
            for rule_name, rule in self.bookkeeping_rules.items():
                if self.matcher_rewriter.exec_on_first_match(od.m, rule, rule_name, in_place=True) is not None:
                    applied[rule_name] += 1
                    changed = True
        return ODAPI(od.state, od.m, od.mm), applied


# copied over from assignment 3 for the render_text function
def get_time(od: ODAPI):
    _, clock = od.get_all_instances("Clock")[0]
    return od.get_slot_value(clock, "time")


def render_text(od: ODAPI):
    # copied from assignment 3
    # Short description of the current state
    parts = []

    # served count per dish, and the total out of the 3 needed to finish the shift
    total_served = 0
    for _, dish_state in od.get_all_instances("DishState"):
        dish = od.get_target(od.get_outgoing(dish_state, "stateOfDish")[0])
        served = od.get_slot_value(dish_state, "served")
        total_served += served
        parts.append(f"{od.get_slot_value(dish, 'dishName')}: {served} served")

    # all open orders with their arrival time
    for order_name, order in od.get_all_instances("Order"):
        dish = od.get_target(od.get_outgoing(order, "OrderDish")[0])
        parts.append(f"{order_name} for {od.get_slot_value(dish, 'dishName')} (arrived at {od.get_slot_value(order, 'arrivedAt')})")

    header = f"[t = {get_time(od)} | {total_served}/3 served]"
    return " - ".join([header] + parts)


def get_filename(name, kind):
    file_dir = os.path.dirname(__file__)
    return f"{file_dir}/rules/r_{name}_{kind}.od"


def get_rules(current_state, rt_mm):
    print("Loading rules")
    rt_mm_ramified = ramify(current_state, rt_mm)
    matcher_rewriter = RuleMatcherRewriter(current_state, rt_mm, rt_mm_ramified)

    action_rules = [load_rules(current_state, get_filename, rt_mm_ramified, names) for names in ACTION_RULES]
    bookkeeping_rules = load_rules(current_state, get_filename, rt_mm_ramified, BOOKKEEPING_RULES)

    return BookkeepingActionGenerator(PriorityActionGenerator(matcher_rewriter, action_rules),
                                      matcher_rewriter, bookkeeping_rules)


state = DevState()
scd_mm = bootstrap_scd(state)

# Static Models
dish_mm = parse_and_check(state, mm_dish, scd_mm, "MM for Dish")
dish_m = parse_and_check(state, m_dish, dish_mm, "Model for Dish")
# Runtime Models
rt_dish_mm = parse_and_check(state, rt_mm_dish, scd_mm, "Runtime MM for Dish")
rt_dish_m = parse_and_check(state, rt_m_dish, rt_dish_mm, "Runtime Model for Dish")

print("About to start the simulation...")
rule_generator = get_rules(state, rt_dish_mm)
rule_sim = KitchenSimulator(
    action_generator=rule_generator,
    termination_condition=TerminationCondition(state, rt_dish_mm),
    renderer=render_text,
    decision_maker=InteractiveDecisionMaker(),
)

dish_od, _ = rule_generator.settle(ODAPI(state, rt_dish_m, rt_dish_mm))
rule_sim.run(dish_od)
