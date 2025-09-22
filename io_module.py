# io_module.py
"""
The Particle Simulator — Модуль ввода/вывода
Сохранение и загрузка миров в формате .tps (TPS Save File)
"""

import os
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Попытка импортировать constants
try:
    from constants import GRID_W, GRID_H, MAX_ELEMENT_ID
except ImportError:
    # Дефолтные значения на случай отсутствия constants
    GRID_W = 1000
    GRID_H = 800
    MAX_ELEMENT_ID = 255

# Версия формата сохранения
SAVE_FORMAT_VERSION = "3.1"

# Список полей, которые нужно сохранять
GRID_FIELDS = [
    'type',           # тип материала
    'temp',           # температура (K)
    'life',           # "жизнь" (огонь, вирусы)
    'vx',             # скорость X
    'vy',             # скорость Y
    'pressure',       # давление (Па)
    'density',        # плотность
    'conductivity',   # проводимость
    'charge',         # заряд
    'radiation',      # радиация
    'damage',         # повреждение клеток
    'age',            # возраст клетки
    'fitness',        # приспособленность
    'telomere',       # длина теломер
]

# Дополнительные скалярные или метаданные поля (не сохраняются как массивы)
META_FIELDS = [
    'simulation_time',
    'author',
    'description',
    'tags',
]


def save_world(grid, filename: str, metadata: Dict[str, Any] = None):
    """
    Сохраняет текущее состояние сетки в файл .tps (TPS Save File).
    
    Args:
        grid: объект Grid с атрибутами type, temp, vx, vy и т.д.
        filename: путь к файлу (например, 'world.tps')
        metadata: дополнительные данные (автор, описание и т.д.)
    """
    if not filename.endswith('.tps'):
        filename += '.tps'

    # Собираем данные для сохранения
    data_arrays = {}
    
    for field in GRID_FIELDS:
        if hasattr(grid, field):
            value = getattr(grid, field)
            if isinstance(value, np.ndarray):
                data_arrays[field] = value.astype(np.float32) if field in ['temp', 'vx', 'vy', 'pressure'] else value
            elif field == 'dna' and value.dtype == object:
                # Специальная обработка DNA (как строки)
                flat_dna = np.array([str(d) for d in value.flat], dtype=object).reshape(value.shape)
                data_arrays[field] = flat_dna
            else:
                print(f"[WARN] Поле {field} не является массивом или не поддерживается")
    
    # Метаданные
    meta = metadata or {}
    meta.update({
        'format': 'TPS',
        'version': SAVE_FORMAT_VERSION,
        'grid_w': GRID_W,
        'grid_h': GRID_H,
        'created_at': datetime.now().isoformat(),
        'element_count': len(np.unique(data_arrays.get('type', [])))
    })

    try:
        with open(filename, 'wb') as f:
            np.savez_compressed(
                f,
                **data_arrays,
                _metadata=json.dumps(meta)
            )
        print(f"[INFO] Мир сохранён: {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить {filename}: {e}")
        return False


def load_world(grid, filename: str) -> bool:
    """
    Загружает мир из файла .tps в существующий объект grid.
    
    Args:
        grid: объект Grid, в который загружаются данные
        filename: путь к файлу
    
    Returns:
        bool: успех загрузки
    """
    if not os.path.exists(filename):
        print(f"[ERROR] Файл не найден: {filename}")
        return False

    try:
        data = np.load(filename, allow_pickle=True)
        
        # Проверка формата
        if '_metadata' not in data:
            print(f"[WARN] Нет метаданных в {filename}. Продолжаем...")
        
        metadata_raw = data.get('_metadata', None)
        metadata = json.loads(metadata_raw) if metadata_raw is not None else {}
        
        if metadata.get('format') != 'TPS':
            print(f"[ERROR] Неверный формат файла: {filename}")
            return False
        
        # Проверка размеров
        saved_w = metadata.get('grid_w')
        saved_h = metadata.get('grid_h')
        if saved_w and saved_h:
            if saved_w != GRID_W or saved_h != GRID_H:
                print(f"[WARN] Размеры сетки не совпадают: {saved_w}x{saved_h} ≠ {GRID_W}x{GRID_H}")
                # Можно добавить auto-resize, но пока просто предупреждаем
        
        # Загружаем поля
        for field in GRID_FIELDS:
            if field in data:
                array = data[field]
                target_attr = getattr(grid, field, None)
                if target_attr is not None and isinstance(target_attr, np.ndarray):
                    try:
                        if array.shape == target_attr.shape:
                            target_attr[:] = array
                        else:
                            # Подгоняем размер (обрезаем или дополняем нулями)
                            h, w = target_attr.shape
                            h_src, w_src = array.shape[:2]
                            h_copy = min(h, h_src)
                            w_copy = min(w, w_src)
                            target_attr[:h_copy, :w_copy] = array[:h_copy, :w_copy]
                        print(f"[OK] Загружено: {field}")
                    except Exception as e:
                        print(f"[ERROR] Ошибка при загрузке {field}: {e}")
                else:
                    print(f"[SKIP] Поле {field} не найдено в объекте grid")
            else:
                print(f"[SKIP] Поле {field} отсутствует в файле")
        
        print(f"[INFO] Мир загружен: {filename}")
        if metadata:
            author = metadata.get('author', 'unknown')
            desc = metadata.get('description', 'Без описания')
            print(f"  Автор: {author}")
            print(f"  Описание: {desc}")
        return True

    except Exception as e:
        print(f"[ERROR] Не удалось загрузить {filename}: {e}")
        return False


def list_saved_worlds(directory: str = ".", extension: str = ".tps") -> list:
    """
    Возвращает список всех файлов сохранений в директории.
    """
    worlds = []
    for file in os.listdir(directory):
        if file.endswith(extension):
            filepath = os.path.join(directory, file)
            stat = os.stat(filepath)
            worlds.append({
                'name': file,
                'size_kb': stat.st_size // 1024,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'path': filepath
            })
    return sorted(worlds, key=lambda x: x['modified'], reverse=True)


def validate_save_file(filename: str) -> Dict[str, Any]:
    """
    Проверяет целостность файла сохранения.
    """
    if not os.path.exists(filename):
        return {'valid': False, 'error': 'Файл не найден'}

    try:
        with np.load(filename, allow_pickle=True) as data:
            if '_metadata' not in data:
                return {'valid': False, 'error': 'Нет метаданных'}
            
            metadata = json.loads(data['_metadata'])
            if metadata.get('format') != 'TPS':
                return {'valid': False, 'error': 'Неверный формат'}
            
            required_fields = ['type']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return {'valid': False, 'error': f'Отсутствуют поля: {missing}'}
            
            return {
                'valid': True,
                'metadata': metadata,
                'fields': [k for k in data.keys() if k != '_metadata'],
                'size': os.path.getsize(filename)
            }
    except Exception as e:
        return {'valid': False, 'error': str(e)}


# === УДОБНЫЕ ОБЁРТКИ ДЛЯ main.py ===

def quick_save(grid, base_name="autosave"):
    """Быстрое сохранение с временной меткой"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{timestamp}.tps"
    return save_world(grid, filename, metadata={'auto': True})


def quick_load_latest(grid, pattern="autosave_*.tps") -> bool:
    """Загружает последний автоматический сейв"""
    import glob
    files = glob.glob(pattern)
    if not files:
        print("[INFO] Автосейвы не найдены")
        return False
    latest = max(files, key=os.path.getmtime)
    return load_world(grid, latest)


# === ТЕСТИРОВАНИЕ ===
if __name__ == "__main__":
    print("🧪 Тестирование io_module.py")

    # Создаём тестовую сетку (если нет настоящей)
    class MockGrid:
        def __init__(self, w=100, h=100):
            self.w, self.h = w, h
            self.type = np.zeros((h, w), dtype=np.uint8)
            self.temp = np.full((h, w), 298.0, dtype=np.float32)
            self.vx = np.zeros((h, w), dtype=np.float32)
            self.vy = np.zeros((h, w), dtype=np.float32)
            self.radiation = np.zeros((h, w), dtype=np.float32)
            self.dna = np.empty((h, w), dtype=object)
            for y in range(h):
                for x in range(w):
                    self.dna[y, x] = "ACGT" if np.random.rand() < 0.1 else ""

    grid = MockGrid(50, 50)

    # Сохраняем
    meta = {
        'author': 'TPS User',
        'description': 'Тестовый мир',
        'tags': ['test', 'physics']
    }
    save_world(grid, "test_world.tps", metadata=meta)

    # Проверяем
    info = validate_save_file("test_world.tps")
    print("Валидация:", info)

    # Загружаем
    new_grid = MockGrid(50, 50)
    load_world(new_grid, "test_world.tps")

    print("✅ Тест завершён.")