# TODO: add your meta-model
mm_dish = """
    Dish:Class{
        constraint = ```
            steps = [get_target(l) for l in get_outgoing(this, "hasStep")]  # collect all steps connected to this dish
            nums = sorted(get_slot_value(step, "number") for step in steps) 
            total_duration = sum(get_slot_value(step, "duration") for step in steps)

            (
                get_slot_value(this, "difficulty") > 0
                and get_slot_value(this, "cooktime") >= 0
                and get_slot_value(this, "serves") > 0
                and nums == list(range(1, len(nums) + 1))   # check if there are no gaps between steps
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

            #actions need a corresponding tool
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

# TODO: add your runtime meta-model
rt_mm_dish = mm_dish + """
    Clock:Class {
        lower_cardinality = 1;
        upper_cardinality = 1;
    }
    Clock_time:AttributeLink (Clock -> Integer) {
        name = "time";
        optional = False;
        constraint = `get_value(get_target(this)) >= 0`;
    }

    Order:Class
    
    Order_arrivedAt:AttributeLink (Order -> Integer){
        name = "arrivedAt";
        optional = False;
    }

    OrderDish:Association (Order -> Dish){
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }

    State:Class {
        abstract = True;
    }
    
    DishState:Class
    :Inheritance (DishState -> State)
    stateOfDish:Association (DishState -> Dish) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }
    DishState_served:AttributeLink (DishState -> Integer){
        name = "served";
        optional = False;
    }
    
    StepState:Class {
        constraint = ```
            result = True
            if get_slot_value(this, "finishedAt") is not None:
                result = get_slot_value(this, "startedAt") < get_slot_value(this, "finishedAt");
                
            result
        ```
    }
    :Inheritance (StepState -> State)
    stateOfStep:Association (StepState -> Step) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }
    StepState_startedAt:AttributeLink (StepState -> Integer){
        name = "startedAt";
        optional = False;
    }
    
    StepState_finishedAt:AttributeLink (StepState -> Integer){
        name = "finishedAt";
        optional = False;
    }
    
    
    ToolState:Class
    :Inheritance (ToolState -> State)
    stateOfTool:Association (ToolState -> Tool) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }
    ToolState_inUse:AttributeLink (ToolState -> Boolean) {
        name = "inUse";
        optional = False;
    }
    
    
    CookState:Class
    :Inheritance (CookState -> State)
    stateOfCook:Association (CookState -> Cook) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }
    CookState_busy:AttributeLink (CookState -> Boolean) {
        name = "busy";
        optional = False;
    }
    
    CookState_lastMovedAt:AttributeLink (CookState -> Integer) {
        name = "lastMovedAt";
        optional = True;
    }

    toolNotDoubleUsed:GlobalConstraint {
        constraint = ```
            result = True
        
            active_step_states = []
            for _, stepState in get_all_instances("StepState"):
                if get_slot(stepState, "finishedAt") is None and get_slot(stepState, "startedAt"):
                    active_step_states.append(stepState)
            
            active_tools = []
            for step_state in active_step_states:
                step = get_outgoing(step_state, "stateOfStep")
                tools = get_outgoing(step, "hasTool")
                for tool_link in tools:
                    tool = get_target(tool_link)
                    if tool in active_tools: 
                        result = False
                    else:
                        active_tools.append(tool)
                    
                    if result = False:
                        break    
                    
            result
        ```
    }
    
    CookNotDoubleBooked:GlobalConstraint {
        constraint = ```
            result = True
        
            active_step_states = []
            for _, stepState in get_all_instances("StepState"):
                if get_slot(stepState, "finishedAt") is None and get_slot(stepState, "startedAt"):
                    active_step_states.append(stepState)
            
            active_cooks = []
            for step_state in active_step_states:
                step = get_outgoing(step_state, "stateOfStep")
                cooks = get_outgoing(step, "hasCook")
                for cook_link in cooks:
                    cook = get_target(cook_link)
                    if cook in active_cooks: 
                        result = False
                    else:
                        active_cooks.append(cook)
                    
                    if result = False:
                        break    
                    
            result
        ```
    }
"""



# TODO: add a valid instance of your meta-model
m_dish = """
"""

# TODO: add a valid instance of your additional runtime information
rt_m_dish = m_dish + """
"""
