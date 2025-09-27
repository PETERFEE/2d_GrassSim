import copy
from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

PLANT_TYPES = {
    "Dirt": {"name": "Dirt", "water_need": 0, "color": "#a1887f", "drought_tolerance": 0, "root_depth": 0, "is_native": False},
    "St. Augustine": {"name": "St. Augustine", "water_need": 15, "color": "#4caf50", "drought_tolerance": 2, "root_depth": 3, "is_native": False},
    "Bermuda": {"name": "Bermuda", "water_need": 12, "color": "#2e7d32", "drought_tolerance": 4, "root_depth": 4, "is_native": False},
    "Buffalo": {"name": "Buffalo", "water_need": 8, "color": "#66bb6a", "drought_tolerance": 6, "root_depth": 5, "is_native": True},
    "Zoysia": {"name": "Zoysia", "water_need": 10, "color": "#8bc34a", "drought_tolerance": 5, "root_depth": 4, "is_native": False},
    "Fescue": {"name": "Fescue", "water_need": 14, "color": "#4caf50", "drought_tolerance": 3, "root_depth": 6, "is_native": False},
    "Wildflowers": {"name": "Wildflowers", "water_need": 5, "color": "#ffeb3b", "drought_tolerance": 7, "root_depth": 2, "is_native": True},
    "Native Grasses": {"name": "Native Grasses", "water_need": 3, "color": "#9ccc65", "drought_tolerance": 8, "root_depth": 8, "is_native": True},
    "Succulents": {"name": "Succulents", "water_need": 2, "color": "#a5d6a7", "drought_tolerance": 9, "root_depth": 1, "is_native": True},
    "Dead": {"name": "Dead", "water_need": 0, "color": "#5d4037", "drought_tolerance": 0, "root_depth": 0, "is_native": False},
}

INITIAL_GAME_STATE = {
    "day": 1,
    "aquifer_level": 100,
    "lawn_grid": [
        {"plant_type": "St. Augustine", "moisture": 50, "root_depth": 3, "health": 100} for _ in range(9)
    ],
    "game_over": False,
    "message": "Welcome to RootDown! Build a drought-tolerant lawn without draining the aquifer.",
    "score": 0,
    "high_score": 0,
    "lawn_settings": {
        "mowing_height": 2.5,  # inches
        "watering_schedule": 3,  # times per week
        "fertilizer_type": "None",
        "last_mowed": 0,  # days since last mowing
    },
    "sinkholes": [],  # List of sinkhole positions
    "total_water_used": 0,
    "native_plant_bonus": 0,
}

# Fertilizer types
FERTILIZER_TYPES = {
    "None": {"name": "None", "water_efficiency": 1.0, "root_growth": 1.0, "cost": 0},
    "Organic": {"name": "Organic", "water_efficiency": 1.2, "root_growth": 1.3, "cost": 5},
    "Slow-Release": {"name": "Slow-Release", "water_efficiency": 1.1, "root_growth": 1.2, "cost": 8},
    "Drought-Resistant": {"name": "Drought-Resistant", "water_efficiency": 1.4, "root_growth": 1.1, "cost": 12},
}

# deep copy to avoid modifying the original constant
game_state = copy.deepcopy(INITIAL_GAME_STATE)

# --- Backend Logic ---
def calculate_score():
    """Calculate the current score based on lawn health and water conservation."""
    global game_state
    
    # Base score from days survived
    base_score = game_state["day"] * 10
    
    # Bonus for healthy plants
    healthy_plants = sum(1 for tile in game_state["lawn_grid"] if tile["plant_type"] not in ["Dead", "Dirt"])
    health_bonus = healthy_plants * 5
    
    # Bonus for native plants
    native_plants = sum(1 for tile in game_state["lawn_grid"] 
                       if PLANT_TYPES.get(tile["plant_type"], {}).get("is_native", False))
    native_bonus = native_plants * 10
    
    # Penalty for water usage (encourage conservation)
    water_penalty = game_state["total_water_used"] * 2
    
    # Bonus for deep roots
    avg_root_depth = sum(tile["root_depth"] for tile in game_state["lawn_grid"]) / len(game_state["lawn_grid"])
    root_bonus = avg_root_depth * 3
    
    game_state["score"] = max(0, base_score + health_bonus + native_bonus + root_bonus - water_penalty)
    
    # Update high score
    if game_state["score"] > game_state["high_score"]:
        game_state["high_score"] = game_state["score"]

def check_game_over():
    """Checks for game over conditions and updates the state."""
    global game_state
    if game_state["game_over"]:
        return

    # Condition 1: Aquifer is empty
    if game_state["aquifer_level"] <= 0:
        game_state["game_over"] = True
        game_state["message"] = "Game Over: The aquifer has run dry! Your score is {} points.".format(game_state["score"])
        return

    # Condition 2: All plants are dead
    if all(tile["plant_type"] == "Dead" for tile in game_state["lawn_grid"]):
        game_state["game_over"] = True
        game_state["message"] = "Game Over: All your plants have died! Your score is {} points.".format(game_state["score"])
        return

def create_sinkhole():
    """Create a sinkhole if aquifer is critically low."""
    global game_state
    if game_state["aquifer_level"] < 20 and len(game_state["sinkholes"]) < 3:
        import random
        # Find an empty spot for sinkhole
        available_spots = [i for i in range(9) if i not in game_state["sinkholes"]]
        if available_spots:
            sinkhole_pos = random.choice(available_spots)
            game_state["sinkholes"].append(sinkhole_pos)
            game_state["message"] = f"Sinkhole appeared at position {sinkhole_pos + 1}! Aquifer critically low!"

def update_root_depth():
    """Update root depth based on mowing practices and fertilizer."""
    global game_state
    mowing_height = game_state["lawn_settings"]["mowing_height"]
    fertilizer = FERTILIZER_TYPES[game_state["lawn_settings"]["fertilizer_type"]]
    
    for tile in game_state["lawn_grid"]:
        if tile["plant_type"] not in ["Dead", "Dirt"]:
            plant_info = PLANT_TYPES[tile["plant_type"]]
            base_root_depth = plant_info["root_depth"]
            
            # Taller mowing encourages deeper roots
            height_bonus = max(0, (mowing_height - 2.0) * 0.5)
            
            # Fertilizer affects root growth
            fertilizer_bonus = fertilizer["root_growth"] - 1.0
            
            # Calculate new root depth
            new_depth = min(10, base_root_depth + height_bonus + fertilizer_bonus)
            tile["root_depth"] = max(1, new_depth)

@app.route('/assets/tiles/<filename>')
def serve_tile(filename):
    """Serve tile images from the assets/tiles directory."""
    return send_from_directory('assets/tiles', filename)

#api destin
@app.route('/')
def index():
    """Serves the main game page."""
    return render_template('index.html')

@app.route('/gamestate')
def get_gamestate():
    """Returns the current state of the game."""
    return jsonify(game_state)

@app.route('/reset', methods=['POST'])
def reset_game():
    """Resets the game to its initial state."""
    global game_state
    game_state = copy.deepcopy(INITIAL_GAME_STATE)
    return jsonify(game_state)

@app.route('/water', methods=['POST'])
def water_lawn():
    """Waters the lawn, consuming aquifer water."""
    global game_state
    if not game_state["game_over"]:
        fertilizer = FERTILIZER_TYPES[game_state["lawn_settings"]["fertilizer_type"]]
        water_amount = int(10 / fertilizer["water_efficiency"])  # More efficient with better fertilizer
        
        if game_state["aquifer_level"] >= water_amount:
            game_state["aquifer_level"] -= water_amount
            game_state["total_water_used"] += water_amount
            
            for tile in game_state["lawn_grid"]:
                if tile["plant_type"] != "Dead" and tile["plant_type"] != "Dirt":
                    # Deeper roots help retain moisture
                    root_bonus = tile["root_depth"] * 2
                    tile["moisture"] = min(100, tile["moisture"] + 30 + root_bonus)
                    tile["health"] = min(100, tile["health"] + 10)
            
            game_state["message"] = f"You watered the lawn. Used {water_amount} water units."
        else:
            game_state["message"] = "Not enough water in the aquifer!"
        
        calculate_score()
        create_sinkhole()
        check_game_over()
    return jsonify(game_state)

@app.route('/plant', methods=['POST'])
def plant():
    """Changes a plant on a specific tile."""
    global game_state
    if not game_state["game_over"]:
        data = request.json
        tile_index = data.get("tile_index")
        plant_name = data.get("plant_name")
        if 0 <= tile_index < len(game_state["lawn_grid"]) and plant_name in PLANT_TYPES:
            plant_info = PLANT_TYPES[plant_name]
            game_state["lawn_grid"][tile_index] = {
                "plant_type": plant_name, 
                "moisture": 50, 
                "root_depth": plant_info["root_depth"],
                "health": 100
            }
            game_state["message"] = f"You planted {plant_name}."
            calculate_score()
    return jsonify(game_state)

@app.route('/nextday', methods=['POST'])
def next_day():
    """Advances the game by one day, simulating evaporation."""
    global game_state
    if not game_state["game_over"]:
        game_state["day"] += 1
        game_state["lawn_settings"]["last_mowed"] += 1
        game_state["message"] = f"A new day has dawned. It is day {game_state['day']}."
        
        # Update root depths based on mowing practices
        update_root_depth()
        
        for tile in game_state["lawn_grid"]:
            plant_info = PLANT_TYPES.get(tile["plant_type"])
            if plant_info:
                # Calculate water loss based on drought tolerance and root depth
                drought_factor = max(0.5, 1.0 - (plant_info["drought_tolerance"] / 10))
                root_factor = max(0.7, 1.0 - (tile["root_depth"] / 20))
                
                water_loss = plant_info["water_need"] * drought_factor * root_factor
                tile["moisture"] = max(0, tile["moisture"] - water_loss)
                
                # Update health based on moisture
                if tile["moisture"] < 20:
                    tile["health"] = max(0, tile["health"] - 15)
                elif tile["moisture"] > 80:
                    tile["health"] = min(100, tile["health"] + 5)
                
                # Plant dies if moisture is 0 or health is 0
                if tile["moisture"] == 0 or tile["health"] == 0:
                    if tile["plant_type"] not in ["Dirt", "Dead"]:
                        tile["plant_type"] = "Dead"
                        tile["health"] = 0
        
        calculate_score()
        create_sinkhole()
        check_game_over()
    return jsonify(game_state)

@app.route('/mow', methods=['POST'])
def mow_lawn():
    """Mow the lawn, improving root depth over time."""
    global game_state
    if not game_state["game_over"]:
        game_state["lawn_settings"]["last_mowed"] = 0
        game_state["message"] = f"Lawn mowed at {game_state['lawn_settings']['mowing_height']} inches height."
        calculate_score()
    return jsonify(game_state)

@app.route('/settings', methods=['POST'])
def update_settings():
    """Update lawn management settings."""
    global game_state
    if not game_state["game_over"]:
        data = request.json
        if "mowing_height" in data:
            game_state["lawn_settings"]["mowing_height"] = max(1.0, min(5.0, float(data["mowing_height"])))
        if "watering_schedule" in data:
            game_state["lawn_settings"]["watering_schedule"] = max(0, min(7, int(data["watering_schedule"])))
        if "fertilizer_type" in data and data["fertilizer_type"] in FERTILIZER_TYPES:
            game_state["lawn_settings"]["fertilizer_type"] = data["fertilizer_type"]
        
        game_state["message"] = "Lawn settings updated."
        calculate_score()
    return jsonify(game_state)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)