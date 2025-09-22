# elements.py
from constants import *

ELEMENTS = {
    # === Газы ===
    0: {"name": "Air", "color": (0,0,0), "state": "gas", "density": 0},
    3: {"name": "WaterVapor", "color": (200,200,255), "state": "gas", "density": 0.8},
    10: {"name": "Hydrogen", "color": (255,255,200), "state": "gas", "density": 0.1, "flammable": 200},
    11: {"name": "Oxygen", "color": (200,220,255), "state": "gas", "density": 1.4, "supports_combustion": True},
    
    # === Жидкости ===
    2: {"name": "Sand", "color": (240,220,80), "state": "solid", "density": 3, "update": "update_sand"},
    3: {"name": "Water", "color": (0,100,255), "state": "liquid", "density": 2, "update": "update_water"},
    15: {"name": "Acid", "color": (200,255,0), "state": "liquid", "density": 2, "corrosive": True},
    
    # === Твёрдые ===
    1: {"name": "Wall", "color": (80,80,80), "state": "solid", "density": 100},
    13: {"name": "Iron", "color": (180,100,50), "state": "solid", "density": 7, "conductivity": 20, "ferromagnetic": True},
    62: {"name": "SteelSpring", "color": (160,160,180), "state": "solid", "density": 7.8, "update": "update_spring", "elastic": True},
    60: {"name": "Rubber", "color": (180,30,30), "state": "solid", "density": 0.92, "update": "update_elastic", "elastic": True},
    
    # === Плазма / Энергия ===
    4: {"name": "Fire", "color": (255,50,5), "state": "plasma", "density": 0, "update": "update_fire", "temp_change": 1000},
    5: {"name": "Smoke", "color": (100,100,100), "state": "gas", "density": 0.5, "update": "update_smoke"},
    8: {"name": "Electron", "color": (255,255,0), "state": "energy", "update": "update_electron", "charge": -1},
    54: {"name": "Neutron", "color": (255,255,255), "state": "particle", "update": "update_neutron"},
    59: {"name": "GammaRay", "color": (255,255,255), "state": "radiation", "update": "update_gamma", "penetration": 50},
    
    # === Биология ===
    100: {"name": "StemCell", "color": (220,180,255), "state": "cell", "update": "update_stem_cell", "dna": True},
    101: {"name": "Neuron", "color": (100,150,255), "state": "cell", "update": "update_neuron", "excitable": True},
    102: {"name": "Muscle", "color": (200,50,50), "state": "cell", "update": "update_muscle", "contractile": True},
    107: {"name": "Virus", "color": (0,255,0), "state": "virus", "update": "update_virus", "infects": [100,101]},
    106: {"name": "Cancer", "color": (255,0,100), "state": "cell", "update": "update_cancer", "uncontrolled_division": True},
    
    # === Ядерные ===
    50: {"name": "Uranium235", "color": (0,180,0), "state": "solid", "radioactive": True, "fissionable": True},
    52: {"name": "Plutonium239", "color": (180,0,0), "state": "solid", "radioactive": True, "fissionable": True},
    60: {"name": "Cesium137", "color": (100,100,200), "state": "solid", "radioactive": True, "half_life": 9467000},
    61: {"name": "Iodine131", "color": (200,50,200), "state": "solid", "radioactive": True, "bio_accumulation": "thyroid"},
    
    # === Инструменты ===
    9: {"name": "Destroy", "color": (255,0,255), "state": "tool", "update": None},
}

def get_element_name(elem_id):
    return ELEMENTS.get(elem_id, {}).get("name", f"Unknown({elem_id})")

def is_liquid_or_gas(state):
    return state in ["liquid", "gas", "plasma"]