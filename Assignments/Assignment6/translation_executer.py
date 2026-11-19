import os
import sys

from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from state.devstate import DevState
from transformation.ramify import ramify
from transformation.rule import RuleMatcherRewriter, ActionGenerator
from util import loader, simulator
from util.simulator import MinimalSimulator

if len(sys.argv) != 2:
    print("Usage:")
    print(f"  python {__file__} model.od")
    print("where `model.od` is a valid instance of RPG+Petri-Net.")
    sys.exit(1)

model_file = sys.argv[1]
state = DevState()
scd_mm = bootstrap_scd(state)

CWD = os.path.dirname(__file__)
with open(f"{CWD}/merged_mm.od") as f:
    model_cs = f.read()

print("Now loading MM")
merged_mm = loader.parse_and_check(state, model_cs, scd_mm, "Merged MM", check_conformance=False)

print("Ramify")
ramified_mm = ramify(state, merged_mm)

rules = loader.load_rules(state, lambda rule, kind: f"{CWD}/petrinet/operational_semantics/r_{rule}_{kind}.od",
                          ramified_mm, ["fire_transition"])

print("Load Model")
with open(f"{CWD}/{model_file}") as f:
    model = loader.parse_and_check(state, f.read(), merged_mm, "Model", check_conformance=False)

print("Ready!")
matcher_rewriter = RuleMatcherRewriter(state, merged_mm, ramified_mm)
action_generator = ActionGenerator(matcher_rewriter, rules)


sim = MinimalSimulator(
    action_generator=action_generator,
    decision_maker=simulator.InteractiveDecisionMaker(auto_proceed=False),
    termination_condition=lambda od: None
)

sim.run(ODAPI(state, model, merged_mm))
