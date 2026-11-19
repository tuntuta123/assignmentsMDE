import os

from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od import renderer
from state.devstate import DevState
from transformation.merger import merge_models
from transformation.topify.topify import Topifier
from util import loader

from models import mm_dish, rt_mm_dish

CWD = os.path.dirname(__file__)


def read_file(filename: str):
    with open(f"{CWD}/{filename}") as f:
        return f.read()


state = DevState()
scd_mm = bootstrap_scd(state)

# Petri Net Models
pn_mm_cs = read_file("petrinet/mm_design.od")
pn_mm = loader.parse_and_check(state, pn_mm_cs, scd_mm, "Petri Net Design MM")
pn_rt_mm = loader.parse_and_check(state, pn_mm_cs + read_file("petrinet/mm_runtime.od"), scd_mm,
                                  "Petri Net Runtime MM")

# Kitchen Models
kitchen_mm = loader.parse_and_check(state, mm_dish, scd_mm, "MM for Kitchen")
rt_rpg_mm = loader.parse_and_check(state, rt_mm_dish, scd_mm, "Runtime MM for Kitchen")

print("## Start Merging ##")
merged_mm_rt = merge_models(state, mm=scd_mm, models=[pn_rt_mm, rt_rpg_mm])
print("Success!")

print("## Topifying ###")
topifier = Topifier(state)
top_merged_mm = topifier.topify_cd(merged_mm_rt)
print("Success!")

top_merged_mm_cs = renderer.render_od(state, top_merged_mm, scd_mm)
with open(f"{CWD}/merged_mm.od", "w") as f:
    f.write("# Auto generated topified runtime Meta-Model, merged Kitchen and Petri Nets")
    f.write(top_merged_mm_cs)
