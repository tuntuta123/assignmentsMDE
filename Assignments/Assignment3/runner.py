from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from state.devstate import DevState
from util.loader import parse_and_check

from models import mm_dish, m_dish, rt_mm_dish, rt_m_dish
from simulator import KitchenSimulator

from assignment3 import get_actions, termination_condition


def render_text(od: ODAPI):
    # TODO: Implement, so a short description of the current state is printed
    txt = ""
    return txt


state = DevState()
scd_mm = bootstrap_scd(state)

# Static Models
dish_mm = parse_and_check(state, mm_dish, scd_mm, "MM for Dish")
dish_m = parse_and_check(state, m_dish, dish_mm, "Model for Dish")
# Runtime Models
rt_dish_mm = parse_and_check(state, rt_mm_dish, scd_mm, "Runtime MM for Dish")
rt_dish_m = parse_and_check(state, rt_m_dish, rt_dish_mm, "Runtime Model for Dish")

print("Going into simulation")
sim = KitchenSimulator(
    action_generator=get_actions,
    termination_condition=termination_condition,
    renderer=render_text
)

dish_od = ODAPI(state, rt_dish_m, rt_dish_mm)
sim.run(dish_od)
