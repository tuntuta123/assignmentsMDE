mm_cs = """
    Dish:Class{
        constraint = ```
            get_slot_value(this, "difficulty") > 0
            get_slot_value(this, "cooktime") >= 0
            get_slot_value(get_slot(this, "serves") > 0
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

    Steps:Class{
        # constraint = '''
        # 
        # ''';    
    }
    
    Step_description:AttributeLink(Steps -> String){
        name="description";
        optional= False;
    }
    
    Step_number:AttributeLink(Steps -> Integer){
        name="number";
        optional= False;
    }
    
    Step_duration:AttributeLink(Steps -> Integer){
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
    
    Stove:Class
    Oven:Class
    Pot:Class
    Knife:Class
    
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