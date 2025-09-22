# mod_loader.py
import json
import os
from typing import Dict, List, Any

def load_mods(mod_dir="mods") -> tuple:
    """
    Загружает все моды из папки mods/
    Возвращает: (elements_dict, reactions_list, custom_physics)
    """
    elements = {}
    reactions = []
    physics_rules = {}
    
    if not os.path.exists(mod_dir):
        print(f"[WARN] Папка {mod_dir} не найдена")
        return elements, reactions, physics_rules
    
    for file in sorted(os.listdir(mod_dir)):
        if not file.endswith(".json"):
            continue
        path = os.path.join(mod_dir, file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[MOD] Загружен: {file}")
                
                # Элементы
                if "elements" in data:
                    for elem_id_str, props in data["elements"].items():
                        elem_id = int(elem_id_str)
                        base = {
                            "name": "Unknown",
                            "color": [255, 255, 255],
                            "state": "void",
                            "density": 0,
                            "update": None
                        }
                        base.update(props)
                        elements[elem_id] = base
                
                # Реакции
                if "reactions" in data:
                    for rxn in data["reactions"]:
                        rxn.setdefault("chance", 1.0)
                        rxn.setdefault("energy_release", 0)
                        rxn.setdefault("explosion", False)
                        reactions.append(rxn)
                
                # Физика
                if "physics" in data:
                    physics_rules.update(data["physics"])
                    
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки {file}: {e}")
    
    return elements, reactions, physics_rules


def validate_elements(elements: Dict[int, dict]):
    """Проверяет корректность элементов"""
    required_keys = ["name", "color", "state"]
    for elem_id, props in elements.items():
        for key in required_keys:
            if key not in props:
                raise ValueError(f"Элемент {elem_id} не имеет '{key}'")
        if not isinstance(props["color"], list) or len(props["color"]) != 3:
            raise ValueError(f"Цвет элемента {elem_id} должен быть [R,G,B]")