# renderer.py
import pygame
import numpy as np
from numba import njit
import os

# Настройки по умолчанию
WINDOW_WIDTH = 1000
PANEL_WIDTH = 200
CELL_SIZE = 1

@njit
def create_base_color_array(grid_type, elements_data, w, h):
    """
    Создаёт базовый массив цветов на основе типа элемента.
    """
    arr = np.zeros((w, h, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            elem_id = grid_type[y, x]
            if elem_id < len(elements_data) and "color" in elements_data[elem_id]:
                color = elements_data[elem_id]["color"]
                arr[x, y, 0] = color[0]
                arr[x, y, 1] = color[1]
                arr[x, y, 2] = color[2]
    return arr

@njit
def apply_thermal_glow(arr, temp, base_temp=298.0):
    """
    Добавляет тепловое свечение: красное/жёлтое при высокой температуре.
    """
    h, w = temp.shape
    for y in range(h):
        for x in range(w):
            delta_t = temp[y, x] - base_temp
            if delta_t > 300:
                intensity = min(delta_t / 2000.0, 1.0)
                # Увеличиваем красный и жёлтый
                arr[x, y, 0] = min(255, int(arr[x, y, 0] + 150 * intensity))
                arr[x, y, 1] = min(255, int(arr[x, y, 1] + 80 * intensity))

@njit
def create_ir_overlay(temp):
    """
    Создаёт ИК-наложение: чем горячее — тем ярче (красно-жёлтое).
    """
    h, w = temp.shape
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    temp_norm = np.clip((temp - 273.0) / 1000.0, 0.0, 1.0)  # 0°C до 1000°C
    overlay[:, :, 0] = (temp_norm.T * 255).astype(np.uint8)      # Красный
    overlay[:, :, 1] = (temp_norm.T * 120).astype(np.uint8)      # Зелёный
    overlay[:, :, 2] = 0                                         # Синий — нет
    return overlay

@njit
def create_pressure_overlay(pressure, base_pressure=101325.0):
    """
    Визуализация давления: красный — избыточное, синий — разрежение.
    """
    h, w = pressure.shape
    diff = (pressure - base_pressure) / 10000.0  # нормализация (10 кПа = 1 шаг)
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            d = diff[y, x]
            if d > 0:
                overlay[x, y, 0] = min(255, int(d * 40))   # красный при избытке
            elif d < 0:
                overlay[x, y, 2] = min(255, int(-d * 40))  # синий при разрежении
    return overlay

@njit
def create_radiation_overlay(radiation):
    """
    Радиационное заражение: зелёное свечение, интенсивность = уровень радиации.
    """
    h, w = radiation.shape
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    rad_norm = np.clip(radiation / 100.0, 0.0, 1.0)
    overlay[:, :, 1] = (rad_norm.T * 220).astype(np.uint8)  # зелёный
    overlay[:, :, 0] = (rad_norm.T * 100).astype(np.uint8)  # красный (для тревоги)
    return overlay

@njit
def create_velocity_overlay(vx, vy, scale=0.5):
    """
    Векторное поле скорости (для жидкостей и газов).
    """
    h, w = vx.shape
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    for y in range(1, h - 1, 3):
        for x in range(1, w - 1, 3):
            speed = np.sqrt(vx[y, x]**2 + vy[y, x]**2) * scale
            if speed > 0.1:
                # Цвет зависит от скорости
                green = min(255, int(speed * 200))
                overlay[x, y, 1] = green
    return overlay

@njit
def create_electric_field_overlay(charge):
    """
    Электрическое поле: положительно — красный, отрицательно — синий.
    """
    h, w = charge.shape
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    max_charge = 100.0
    for y in range(h):
        for x in range(w):
            c = charge[y, x]
            if c > 1:
                overlay[x, y, 0] = min(255, int(c / max_charge * 255))
            elif c < -1:
                overlay[x, y, 2] = min(255, int(-c / max_charge * 255))
    return overlay

@njit
def create_magnetic_field_overlay(bx, by):
    """
    Магнитное поле: направление и напряжённость.
    """
    h, w = bx.shape
    overlay = np.zeros((w, h, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            strength = np.sqrt(bx[y, x]**2 + by[y, x]**2)
            if strength > 0.1:
                overlay[x, y, 0] = min(255, int(strength * 50))
                overlay[x, y, 1] = min(255, int(strength * 30))
    return overlay

class Renderer:
    """
    Высокопроизводительный рендерер с поддержкой научных режимов.
    """
    
    def __init__(self, screen, grid, elements, cell_size=1):
        self.screen = screen
        self.grid = grid
        self.elements = elements
        self.cell_size = cell_size
        self.modes = {
            'normal': True,
            'ir': False,
            'pressure': False,
            'radiation': False,
            'velocity': False,
            'electric': False,
            'magnetic': False
        }
        self.surface_array = None
        self.last_scaled_size = None
        self.render_surface = None
        
        # Проверка, можно ли использовать surfarray
        if not pygame.surfarray.get_arraytype():
            pygame.surfarray.use_arraytype('numpy')

    def toggle_mode(self, mode_name):
        """Переключает режим отображения."""
        if mode_name == 'normal':
            self.modes = {'normal': True}
        else:
            # Только один "научный" режим одновременно
            if self.modes.get(mode_name, False):
                self.modes['normal'] = True
            else:
                self.modes = {'normal': False}
            self.modes[mode_name] = not self.modes.get(mode_name, False)

    def get_active_mode(self):
        """Возвращает активный режим."""
        for mode, active in self.modes.items():
            if active and mode != 'normal':
                return mode
        return 'normal'

    def render(self, grid, screen):
        """
        Основной метод отрисовки.
        """
        sim_width = screen.get_width() - PANEL_WIDTH
        sim_height = screen.get_height()
        grid_w = grid.w
        grid_h = grid.h

        # Масштабирование
        scale_x = sim_width / grid_w
        scale_y = sim_height / grid_h
        target_size = (sim_width, sim_height)

        # === 1. Создание базового изображения ===
        base_arr = create_base_color_array(grid.type, self.elements, grid_w, grid_h)
        
        # Применяем тепловое свечение
        apply_thermal_glow(base_arr, grid.temp)

        # Преобразуем в surface
        base_surface = pygame.surfarray.make_surface(base_arr)
        scaled_surface = pygame.transform.scale(base_surface, target_size)
        screen.blit(scaled_surface, (PANEL_WIDTH, 0))

        # === 2. Наложение режимов ===
        active_mode = self.get_active_mode()

        if active_mode == 'ir':
            ir_overlay = create_ir_overlay(grid.temp)
            overlay_surf = pygame.surfarray.make_surface(ir_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(180)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        elif active_mode == 'pressure':
            p_overlay = create_pressure_overlay(grid.pressure)
            overlay_surf = pygame.surfarray.make_surface(p_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(160)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        elif active_mode == 'radiation':
            r_overlay = create_radiation_overlay(grid.radiation)
            overlay_surf = pygame.surfarray.make_surface(r_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(170)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        elif active_mode == 'velocity':
            v_overlay = create_velocity_overlay(grid.vx, grid.vy)
            overlay_surf = pygame.surfarray.make_surface(v_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(150)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        elif active_mode == 'electric':
            e_overlay = create_electric_field_overlay(grid.charge)
            overlay_surf = pygame.surfarray.make_surface(e_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(160)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        elif active_mode == 'magnetic':
            m_overlay = create_magnetic_field_overlay(grid.magnetic_field_x, grid.magnetic_field_y)
            overlay_surf = pygame.surfarray.make_surface(m_overlay)
            overlay_scaled = pygame.transform.scale(overlay_surf, target_size)
            overlay_scaled.set_alpha(160)
            screen.blit(overlay_scaled, (PANEL_WIDTH, 0))

        # === 3. Отладочные слои (опционально) ===
        # Пример: показ границ клеток (для биологии)
        # pygame.draw.rect(screen, (50, 50, 50), (PANEL_WIDTH, 0, sim_width, sim_height), 1)

    def capture_frame(self, filename="frame.png"):
        """
        Сохраняет текущий кадр как PNG.
        """
        pygame.image.save(self.screen, filename)

    def to_surface(self, grid_part=None):
        """
        Возвращает surface для сохранения или обработки.
        """
        if grid_part is None:
            grid_part = self.grid.type
        arr = create_base_color_array(grid_part, self.elements, grid_part.shape[1], grid_part.shape[0])
        return pygame.surfarray.make_surface(arr)