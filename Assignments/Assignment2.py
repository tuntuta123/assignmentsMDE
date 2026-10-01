mm_cs = """
    Dish:Class{
        constraint = ```
            get_slot_value(this, "difficulty") < 0
            get_slot_value(this, "cooktime") > 0
            get_slot_value(get_slot(this, "serves") < 0
        ```;    
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
        name="difficulty";
        optional= False;
    }

    Steps:Class{
        constraint = '''

        ''';    
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

"""