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
            cooks_meet_skill_level = True
            for cook_link in get_outgoing(this, "hasCook"):
                if get_slot_value(get_target(cook_link), "skillLevel") < dish_difficulty:
                    cooks_meet_skill_level = False

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
                and (action != "Cooking" or "Stove" in tools)
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
    
    Steak:Class
    Vegetable:Class
    Noodles:Class
    Salt:Class
    Water:Class
    Flour:Class
    
    :Inheritance (Noodles -> Ingredient)
    :Inheritance (Salt -> Ingredient)
    :Inheritance (Water -> Ingredient)
    :Inheritance (Flour -> Ingredient)
    :Inheritance (Steak -> Ingredient)
    :Inheritance (Vegetable -> Ingredient)
    
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

conforming_model = """
    boiledNoodles:Dish {
    dishName = "boiled noodles";
    difficulty = 1;
    cooktime = 15; #minutes
    serves = 2;
    }

    chef:Cook {
    name = "Freddy";
    skillLevel = 1;
    }

    pot:Pot
    stove:Stove

    water:Water {
        unit = "liter";
        amount = 2;
    }
    noodles:Noodles {
        unit = "grams";
        amount = 200;
    }
    salt:Salt {
        unit = "grams";
        amount = 5;
    }

    cooking:Cooking {
        attended = True;
    }
    mixing:Mixing {
        attended = True;
    }

    step1:Step {
        number = 1;
        description = "Boil water and cook the noodles";
        duration = 10;
    }

    step2:Step {
        number = 2;
        description = "add salt and mix";
        duration = 2;
    }

    :hasStep (boiledNoodles -> step1)
    :hasStep (boiledNoodles -> step2)

    :nextStep (step1 -> step2)

    :hasAction (step1 -> cooking)
    :hasAction (step2 -> mixing)

    :hasCook (step1 -> chef)
    :hasCook (step2 -> chef)

    :hasIngredient (step1 -> water)
    :hasIngredient (step1 -> noodles)
    :hasIngredient (step2 -> salt)

    :hasTool (step1 -> pot)
    :hasTool (step1 -> stove)
    :hasTool (step2 -> pot)

"""

non_conforming_model = """
    fajita:Dish {
        dishName = "beef fajita";
        difficulty = 2;
        cooktime = 45;
        serves = 1;
    }

    #non conform, he will probably burn the food
    chef:Cook {
        name = "Jimmy";
        skillLevel = 1;
    }

    pot:Pot
    stove:Stove
    knife:Knife

    steak:Steak {
        unit = "grams";
        amount = 350;
    }

    vegetable:Vegetable {
        unit = "cups";
        amount = 1;
    }

    cooking:Cooking {
        attended = True;
    }

    cutting:Cutting {
        attended = True;
    }

    badStep1:Step {
        number = 1;
        description = "Slice the beef and the vegetables";
        duration = 15;
    }

    badStep2:Step {
        number = 2;
        description = "Cook the steak";
        duration = 5;
    }

    badStep3:Step {
        number = 3;
        description = "Add the vegetables and continue";
        duration = 5;
    }

    :hasStep (fajita -> badStep1)
    :hasStep (fajita -> badStep2)
    :hasStep (fajita -> badStep3)

    :nextStep (badStep1 -> badStep2)   
    :nextStep (badStep2 -> badStep3)

    :hasAction (badStep1 -> cutting)
    :hasAction (badStep2 -> cooking)
    :hasAction (badStep3 -> cooking)

    #should fail
    :hasCook (badStep1 -> chef)
    :hasCook (badStep2 -> chef)
    :hasCook (badStep3 -> chef)

    :hasIngredient (badStep1 -> steak)
    :hasIngredient (badStep1 -> vegetable)
    :hasIngredient (badStep2 -> steak)
    :hasIngredient (badStep3 -> steak)
    :hasIngredient (badStep3 -> vegetable)

    :hasTool (badStep1 -> knife)
    :hasTool (badStep2 -> pot)
    :hasTool (badStep2 -> stove)
    :hasTool (badStep3 -> pot)
    :hasTool (badStep3 -> stove)

"""
m_conform = parser.parse_od(state, m_text=conforming_model, mm=mm)
m_nonconform = parser.parse_od(state, m_text=non_conforming_model, mm=mm)

# does our model conform to the mm?
conf = Conformance(state, m_conform, mm)
non_conf = Conformance(state, m_nonconform, mm)
print(render_conformance_check_result(conf.check_nominal()))
print(render_conformance_check_result(non_conf.check_nominal()))


#added seperate uml's because they didn't fit
uml_mm = plantuml.render_package(
    "Meta-model",
    plantuml.render_class_diagram(state, mm)
)

uml_conform = plantuml.render_package(
    "Conforming",
    plantuml.render_object_diagram(state, m_conform, mm)
)

uml_nonconform = plantuml.render_package(
    "Non-conforming",
    plantuml.render_object_diagram(state, m_nonconform, mm)
)

print("Meta-model:", make_url(uml_mm))
print("\n")
print("Conforming model:", make_url(uml_conform))
print("\n")
print("Non-conforming model:", make_url(uml_nonconform))