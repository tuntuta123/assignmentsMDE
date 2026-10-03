mm_cs = """
    Dish:Class{
        constraint = ```
            steps = [get_target(l) for l in get_outgoing(this, "hasStep")]  # collect all steps connected to this dish
            nums = sorted(get_slot_value(step, "number") for step in steps) 
            total_duration = sum(get_slot_value(step, "duration") for step in steps)

            (
                get_slot_value(this, "difficulty") > 0
                and get_slot_value(this, "cooktime") >= 0
                and get_slot_value(this, "serves") > 0
                and nums == list(range(1, len(nums) + 1))
                and total_duration <= get_slot_value(this, "cooktime")
                and sum(len(get_outgoing(s, "nextStep")) for s in steps) == len(steps) - 1 # silly check for step count
            )
        ```;
    }

    Dish_dishName:AttributeLink(Dish -> String){
        name = "dishName";
        optional = False;
    }

    Dish_difficulty:AttributeLink(Dish -> Integer){
        name="difficulty";
        optional= False;
    }

    Dish_cooktime:AttributeLink(Dish -> Integer){
        name="cooktime";
        optional= False;
    }

    Dish_serves:AttributeLink(Dish -> Integer){
        name="serves";
        optional= False;
    }

    Step:Class {
        constraint = ```
            dish = get_source(get_incoming(this, "hasStep")[0])
            dish_difficulty = get_slot_value(dish, "difficulty")
            
            # all cooks need to be skilled enough for the dish
            cooks_meet_skill_level = all(
                get_slot_value(get_target(cook_link), "skillLevel") >= dish_difficulty
                for cook_link in get_outgoing(this, "hasCook")
            )

            #action and tool corresp
            action = get_type_name(get_target(get_outgoing(this, "hasAction")[0]))
            tools = [get_type_name(get_target(l)) for l in get_outgoing(this, "hasTool")]
            (
                get_slot_value(this, "number") >= 1
                and get_slot_value(this, "duration") >= 0
                and cooks_meet_skill_level
                and (action != "Cutting" or "Knife" in tools)
                and (action != "Baking" or "Oven" in tools)
                and (action != "Mixing" or "Pot" in tools)
            )
        ```;
    }
    
    Step_description:AttributeLink(Step -> String){
        name="description";
        optional= False;
    }
    
    Step_number:AttributeLink(Step -> Integer){
        name="number";
        optional= False;
    }
    
    Step_duration:AttributeLink(Step -> Integer){
        name="duration";
        optional= False;
    }

    Action:Class {
        abstract = True;
    }
    
    Cutting:Class
    Cooking:Class
    Mixing:Class
    Baking:Class
    
    :Inheritance (Cutting -> Action)
    :Inheritance (Cooking -> Action)
    :Inheritance (Mixing -> Action)
    :Inheritance (Baking -> Action)
    
    Action_attended:AttributeLink(Action -> Boolean){
        name="attended";
        optional = False;
    }

    Ingredient:Class {
        abstract = True;
        constraint = ```
            get_slot_value(this, "amount") > 0
        ```;
    }
    
    Noodles:Class
    Salt:Class
    Water:Class
    Flour:Class
    
    :Inheritance (Noodles -> Ingredient)
    :Inheritance (Salt -> Ingredient)
    :Inheritance (Water -> Ingredient)
    :Inheritance (Flour -> Ingredient)
    
    Ingredient_unit:AttributeLink(Ingredient -> String){
        name = "unit";
        optional = False;
    }
    
    Ingredient_amount:AttributeLink(Ingredient -> Integer){
        name = "amount";
        optional = False;
    }
    
    Tool:Class {
        abstract = True;
    }
    
    Stove:Class {
        upper_cardinality = 4;
    }
    Oven:Class {
        upper_cardinality = 1;
    }
    Pot:Class {
        upper_cardinality = 6;
    }
    Knife:Class {
        upper_cardinality = 6;
    }
    
    :Inheritance (Stove -> Tool)
    :Inheritance (Oven -> Tool)
    :Inheritance (Pot -> Tool)
    :Inheritance (Knife -> Tool)
    
    Cook:Class {
        constraint = ```
            get_slot_value(this, "skillLevel") >= 0
        ```;
    }
    
    Cook_name:AttributeLink(Cook -> String){
        name = "name";
        optional = False;
    }
    
    Cook_skillLevel:AttributeLink(Cook -> Integer){
        name = "skillLevel";
        optional = False;
    }

    #associations

    hasStep:Association (Dish -> Step) {
        target_lower_cardinality = 1;
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
    }

    nextStep:Association (Step -> Step) {
        target_upper_cardinality = 1;
        source_upper_cardinality = 1;
    }

    hasAction:Association (Step -> Action) {
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }

    hasCook:Association (Step -> Cook) {
        target_lower_cardinality = 1;
    }

    hasIngredient:Association (Step -> Ingredient)

    hasTool:Association (Step -> Tool)
    
"""

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od import parser
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url

state = DevState()

mmm = bootstrap_scd(state)

mm = parser.parse_od(state, m_text=mm_cs, mm=mmm)

# does the metamodel conform with the mmm?
conf = Conformance(state, mm, mmm)
print(render_conformance_check_result(conf.check_nominal()))

uml = (""
       + plantuml.render_package("Meta-model", plantuml.render_class_diagram(state, mm))    # render our meta model
       )

print()
print("PlantUML output:", make_url(uml))