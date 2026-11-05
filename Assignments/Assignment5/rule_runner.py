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

        patterns_cs = {
            # TODO: add termination condition patterns, key = reason, value = pattern
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


def render_text(od: ODAPI):
    txt = ""
    # TODO: add in your rendering function (reuse from assignment 3 is valid)
    return txt


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
