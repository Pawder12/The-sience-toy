# main.py
"""
The Particle Simulator — Ultimate Science Edition
(c) 2025 | Профессиональный симулятор материи на Python
"""

import os
import sys
import time
import numpy as np

# Критично для PyInstaller
os.environ['SDL_AUDIODRIVER'] = 'dummy'
if getattr(sys, 'frozen', False):
    import numpy

import pygame
from numba import jit

# === ЛОКАЛЬНЫЕ МОДУЛИ ===
try:
    from grid import Grid
    from mod_loader import load_mods
    from simulator import step_simulation
    from renderer import Renderer
    from ui import UI
    from io_module import save_world, load_world
    from constants import *
except ImportError as e:
    print(f"[ERROR] Не удалось импортировать модуль: {e}")
    sys.exit(1)

# === ИНИЦИАЛИЗАЦИЯ PYGAME ===
pygame.init()
pygame.display.set_caption("The Particle Simulator — Ultimate Science Edition")
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

# === ЗАГРУЗКА МОДОВ ===
print("[INFO] Загрузка модов из папки 'mods/'...")
try:
    ELEMENTS, REACTIONS, PHYSICS_RULES = load_mods("mods")
    if not ELEMENTS:
        raise ValueError("Нет элементов. Проверь папку mods/")
    print(f"[OK] Загружено: {len(ELEMENTS)} элементов, {len(REACTIONS)} реакций.")
except Exception as e:
    print(f"[FATAL] Ошибка загрузки модов: {e}")
    print("Создаю базовые элементы...")
    ELEMENTS = {
        0: {"name": "Air", "color": [0, 0, 0], "state": "gas"},
        1: {"name": "Wall", "color": [80, 80, 80], "state": "solid"},
        2: {"name": "Sand", "color": [240, 220, 80], "state": "solid", "update": "update_sand"},
        3: {"name": "Water", "color": [0, 100, 255], "state": "liquid", "update": "update_water"},
        4: {"name": "Fire", "color": [255, 50, 5], "state": "plasma", "update": "update_fire"},
    }
    REACTIONS = []
    PHYSICS_RULES = {}

# === СОЗДАНИЕ КОМПОНЕНТОВ ===
grid = Grid(GRID_W, GRID_H)
renderer = Renderer(screen, grid, ELEMENTS)
ui = UI(grid, ELEMENTS)

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
running = True
placing = False
erasing = False
last_mx, last_my = -1, -1
show_fps = True
simulation_paused = False
autosave_timer = 0
AUTOSAVE_INTERVAL = 600  # каждые 10 секунд при 60 FPS
debug_mode = False
step_once = False  # Одиночный шаг (при паузе)

print("[INFO] Симуляция запущена. Добро пожаловать в TPS!")

# === ОСНОВНОЙ ЦИКЛ ===
while running:
    mx, my = pygame.mouse.get_pos()
    dt = clock.tick(FPS)
    autosave_timer += 1

    # === СБОР СТАТИСТИКИ ===
    current_fps = clock.get_fps()

    # === СОБЫТИЯ ===
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # Пауза
            if event.key == pygame.K_SPACE:
                simulation_paused = not simulation_paused
                ui.add_notification(f"Симуляция: {'пауза' if simulation_paused else 'запущена'}")

            # Пошаговый режим
            elif event.key == pygame.K_PERIOD and simulation_paused:
                step_once = True
                ui.add_notification("Выполнен один шаг")

            # Режимы отображения
            elif event.key == pygame.K_i:
                renderer.toggle_mode('ir')
                mode = "IR" if renderer.modes['ir'] else "Normal"
                ui.add_notification(f"Режим: {mode}")

            elif event.key == pygame.K_p:
                renderer.toggle_mode('pressure')
                mode = "Pressure" if renderer.modes['pressure'] else "Normal"
                ui.add_notification(f"Режим: {mode}")

            elif event.key == pygame.K_r:
                renderer.toggle_mode('radiation')
                mode = "Radiation" if renderer.modes['radiation'] else "Normal"
                ui.add_notification(f"Режим: {mode}")

            elif event.key == pygame.K_v:
                renderer.toggle_mode('velocity')
                mode = "Velocity" if renderer.modes['velocity'] else "Normal"
                ui.add_notification(f"Режим: {mode}")

            # Сохранение / Загрузка
            elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    save_world(grid, "autosave.tps")
                    ui.add_notification("Сохранено: autosave.tps")
                except Exception as e:
                    ui.add_notification(f"Ошибка сохранения", error=True)

            elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    load_world(grid, "autosave.tps")
                    ui.add_notification("Загружено: autosave.tps")
                except Exception as e:
                    ui.add_notification(f"Ошибка загрузки", error=True)

            # Отладка
            elif event.key == pygame.K_F3:
                debug_mode = not debug_mode
                ui.add_notification(f"Отладка: {'вкл' if debug_mode else 'выкл'}")

            # Очистка
            elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                grid.clear()
                ui.add_notification("Сетка очищена")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                if mx < PANEL_WIDTH:
                    selected = ui.handle_click(mx, my)
                    if selected is not None:
                        ui.selected_element = selected
                        elem_name = ELEMENTS[selected]["name"]
                        ui.add_notification(f"Выбрано: {elem_name}")
                else:
                    placing = True
                    last_mx, last_my = mx, my
                    ui.brush_preview.hide()

            elif event.button == 3:  # ПКМ — ластик
                erasing = True
                ui.selected_element_backup = ui.selected_element
                ui.selected_element = DIS  # Destroy
                ui.brush_preview.hide()

            elif event.button == 4:  # Колесо вверх
                ui.brush_size = min(ui.brush_size + 1, 50)
            elif event.button == 5:  # Колесо вниз
                ui.brush_size = max(ui.brush_size - 1, 1)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                placing = False
            elif event.button == 3:
                erasing = False
                if hasattr(ui, 'selected_element_backup'):
                    ui.selected_element = ui.selected_element_backup

        elif event.type == pygame.MOUSEMOTION:
            if placing or erasing:
                ui.brush_preview.hide()  # Обновляем каждый раз
            ui.brush_preview.show(mx, my, ui.brush_size * CELL_SIZE)

        # Передаём событие в UI
        ui.handle_event(event, renderer)

    # === ОБНОВЛЕНИЕ СИМУЛЯЦИИ ===
    if not simulation_paused or step_once:
        start_time = time.perf_counter()

        # Применяем изменения от мыши
        if placing or erasing:
            elem_id = ui.selected_element
            radius = ui.brush_size
            center_x = (mx - PANEL_WIDTH) // CELL_SIZE
            center_y = my // CELL_SIZE

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = center_x + dx, center_y + dy
                    if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= radius * radius:
                            if elem_id == DIS:
                                grid.type[ny, nx] = AIR
                            else:
                                grid.type[ny, nx] = elem_id
                                if elem_id == FIRE:
                                    grid.life[ny, nx] = 30
                                    grid.temp[ny, nx] = 1500
                                elif "conductivity" in ELEMENTS.get(elem_id, {}):
                                    cond = ELEMENTS[elem_id]["conductivity"]
                                    if cond > 0:
                                        grid.conductivity[ny, nx] = cond

        # Шаг физики
        step_simulation(grid, ELEMENTS, REACTIONS, PHYSICS_RULES)

        step_once = False

        sim_time = (time.perf_counter() - start_time) * 1000
        if debug_mode and current_fps > 0:
            print(f"Step: {sim_time:.2f} ms | FPS: {current_fps:.1f}")

    # === АВТОСОХРАНЕНИЕ ===
    if autosave_timer >= AUTOSAVE_INTERVAL:
        try:
            save_world(grid, "autosave.tps")
            ui.add_notification("Автосохранение", duration=90)
        except:
            ui.add_notification("Ошибка автосохранения", error=True)
        autosave_timer = 0

    # === ОТРИСОВКА ===
    screen.fill((0, 0, 0))

    # Основная симуляция
    renderer.render(grid, screen)

    # Интерфейс
    ui.draw(screen, mx, my, renderer, clock)

    # Показ FPS
    if show_fps:
        fps_text = ui.font_small.render(f"FPS: {int(current_fps)}", True, (0, 255, 0))
        screen.blit(fps_text, (10, 10))

    pygame.display.flip()

# === ЗАВЕРШЕНИЕ ===
print("[INFO] Симуляция завершена. До новых запусков!")
pygame.quit()
sys.exit(0)