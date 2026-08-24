import tkinter as tk
import random
import math
import time
from collections import deque

# ==================== 性能优化工具 ====================
class PerformanceMonitor:
    """性能监控器"""
    def __init__(self):
        self.frame_times: deque[float] = deque(maxlen=60)
        self.start_time: float = time.time()
        self.frame_count: int = 0
        self.fps: float = 0
        self.frame_start: float = 0.0
    
    def start_frame(self) -> None:
        self.frame_start = time.time()
    
    def end_frame(self) -> None:
        if not hasattr(self, 'frame_start') or self.frame_start == 0:
            return
        self.frame_count += 1
        frame_time = time.time() - self.frame_start
        self.frame_times.append(frame_time)
        
        if time.time() - self.start_time >= 1.0:
            self.fps = self.frame_count / (time.time() - self.start_time)
            self.start_time = time.time()
            self.frame_count = 0
    
    def get_fps(self):
        return self.fps
    
    def get_avg_frame_time(self):
        if self.frame_times:
            return sum(self.frame_times) / len(self.frame_times)
        return 0

# ==================== 数据结构 ====================
class AudioSimulator:
    """模拟音频数据生成器"""
    def __init__(self, num_bands=64):
        self.num_bands = num_bands
        self.freq_data = [random.random() for _ in range(1024)]
        self.band_energy = [0.0] * num_bands
        self.smoothing = 0.9
        self.time = 0
        self.beat = 0
        self.beat_counter = 0
        
    def update(self):
        self.time += 0.1
        
        # 模拟节拍
        self.beat_counter += 1
        if self.beat_counter >= random.randint(10, 30):
            self.beat = 1.0
            self.beat_counter = 0
        else:
            self.beat = max(0, self.beat - 0.1)
        
        for i in range(len(self.freq_data)):
            base = math.sin(self.time + i * 0.01) * 0.5 + 0.5
            harmonic = math.sin(self.time * 2 + i * 0.02) * 0.3
            noise = random.uniform(-0.1, 0.1)
            lfo = math.sin(self.time * 0.5) * 0.2
            
            new_value = base * 0.4 + harmonic * 0.3 + noise * 0.1 + lfo + 0.1
            self.freq_data[i] = self.freq_data[i] * 0.8 + new_value * 0.2
        
        bands_per_channel = 1024 // self.num_bands
        for band in range(self.num_bands):
            start = band * bands_per_channel
            end = min(start + bands_per_channel, 1024)
            band_energy = sum(self.freq_data[start:end]) / (end - start)
            self.band_energy[band] = (self.band_energy[band] * self.smoothing + 
                                     band_energy * (1 - self.smoothing))
    
    def get_band_energy(self, band_idx):
        if 0 <= band_idx < len(self.band_energy):
            return self.band_energy[band_idx]
        return 0
    
    def get_full_spectrum(self):
        return self.freq_data
    
    def get_beat(self):
        return self.beat

# ==================== 可视化效果基类 ====================
class VisualEffect:
    """可视化效果基类"""
    def __init__(self, canvas, width, height, audio_sim):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.audio = audio_sim
        self.time = 0
        self.center_x = width // 2
        self.center_y = height // 2
        
    def update(self, dt):
        self.time += dt
        
    def draw(self):
        raise NotImplementedError
    
    def hsv_to_rgb(self, h, s, v):
        """HSV转RGB颜色"""
        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
    
    def get_energy_color(self, energy, hue_offset=0.0):
        """根据能量获取颜色"""
        hue = (0.7 - energy * 0.5 + hue_offset) % 1.0
        saturation = 0.8
        value = 0.3 + energy * 0.7
        return self.hsv_to_rgb(hue, saturation, value)

# ==================== 缺失效果类补全 ====================

class BarsEffect(VisualEffect):
    """条形图效果"""
    def draw(self):
        num_bars = 32
        bar_width = self.width / num_bars
        
        for i in range(num_bars):
            energy = self.audio.get_band_energy(i % 64)
            bar_height = energy * self.height * 0.8
            
            x = i * bar_width
            y = self.height - bar_height
            
            hue = (i / num_bars + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.8)
            
            self.canvas.create_rectangle(x, y, x + bar_width - 2, self.height, fill=color, outline=color)


class SpikesEffect(VisualEffect):
    """尖峰效果"""
    def draw(self):
        num_spikes = 64
        center_x = self.width // 2
        center_y = self.height // 2
        
        for i in range(num_spikes):
            angle = (i / num_spikes) * math.pi * 2
            energy = self.audio.get_band_energy(i % 64)
            spike_length = 50 + energy * 150
            
            x1 = center_x + math.cos(angle) * 30
            y1 = center_y + math.sin(angle) * 30
            x2 = center_x + math.cos(angle) * spike_length
            y2 = center_y + math.sin(angle) * spike_length
            
            hue = (i / num_spikes + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.9)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)


class WaveformEffect(VisualEffect):
    """波形效果"""
    def draw(self):
        points = []
        for i in range(100):
            x = (i / 99) * self.width
            freq_idx = int((i / 99) * 64)
            energy = self.audio.get_band_energy(freq_idx)
            y = self.center_y + math.sin(i * 0.1 + self.time * 3) * (50 + energy * 100)
            points.extend([x, y])
        
        hue = self.time * 0.1 % 1.0
        color = self.hsv_to_rgb(hue, 0.7, 0.9)
        self.canvas.create_line(*points, fill=color, width=2)
        
        points2 = []
        for i in range(100):
            x = (i / 99) * self.width
            freq_idx = int((i / 99) * 64)
            energy = self.audio.get_band_energy(freq_idx)
            y = self.center_y + math.cos(i * 0.1 + self.time * 2) * (40 + energy * 80)
            points2.extend([x, y])
        
        color2 = self.hsv_to_rgb((hue + 0.5) % 1.0, 0.7, 0.9)
        self.canvas.create_line(*points2, fill=color2, width=2)


class VortexEffect(VisualEffect):
    """漩涡效果"""
    def draw(self):
        num_particles = 100
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2 + self.time
            radius = 50 + (i % 32) * 5 + math.sin(self.time * 2 + i) * 20
            energy = self.audio.get_band_energy(i % 64)
            
            x = self.center_x + math.cos(angle) * radius * (1 + energy * 0.5)
            y = self.center_y + math.sin(angle) * radius * (1 + energy * 0.5)
            
            hue = (i / num_particles + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.8)
            size = 3 + energy * 5
            
            self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline=color)


class SpectrumCircleEffect(VisualEffect):
    """频谱环效果"""
    def draw(self):
        num_points = 72
        for ring in range(3):
            ring_radius = 80 + ring * 40
            points = []
            
            for i in range(num_points):
                angle = (i / num_points) * math.pi * 2
                band_idx = int(i * 64 / num_points)
                energy = self.audio.get_band_energy(band_idx)
                
                r = ring_radius + energy * 30
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.extend([x, y])
            
            hue = (ring * 0.3 + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.7, 0.8)
            self.canvas.create_line(*points, fill=color, width=2)


class MatrixRainEffect(VisualEffect):
    """矩阵雨效果"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.drops = [[random.randint(0, height) for _ in range(2)] for _ in range(50)]
    
    def draw(self):
        char_set = "01アイウエオカキクケコ"
        for i, drop in enumerate(self.drops):
            x = (i / len(self.drops)) * self.width
            energy = self.audio.get_band_energy(i % 64)
            y = drop[0]
            char = char_set[int(y / self.height * len(char_set)) % len(char_set)]
            
            hue = (i / len(self.drops) + 0.3) % 1.0
            brightness = 0.3 + energy * 0.7
            color = self.hsv_to_rgb(hue, 0.9, brightness)
            
            self.canvas.create_text(x, y, text=char, fill=color, font=("Consolas", 14))
            
            drop[0] = (drop[0] + 5 + energy * 10) % self.height


class PlasmaEffect(VisualEffect):
    """等离子效果"""
    def draw(self):
        for x in range(0, self.width, 20):
            for y in range(0, self.height, 20):
                v1 = math.sin(x * 0.01 + self.time)
                v2 = math.sin((y * 0.01 + self.time) * 0.5)
                v3 = math.sin((x * 0.01 + y * 0.01 + self.time) * 0.5)
                value = (v1 + v2 + v3) / 3
                
                energy = self.audio.get_band_energy((x + y) % 64)
                hue = (value + 1) * 0.5 + energy * 0.2
                color = self.hsv_to_rgb(hue % 1.0, 0.8, 0.6)
                
                self.canvas.create_rectangle(x, y, x + 18, y + 18, fill=color, outline=color)


class WaterfallEffect(VisualEffect):
    """瀑布图效果"""
    def draw(self):
        num_bands = 64
        band_width = self.width / num_bands
        
        for band in range(num_bands):
            energy = self.audio.get_band_energy(band)
            
            for level in range(10):
                y = self.height - (level + 1) * (self.height / 10)
                alpha = 1.0 - level * 0.1
                bar_height = energy * self.height * 0.8 * alpha
                
                hue = (band / num_bands + self.time * 0.05) % 1.0
                saturation = 0.7 + level * 0.03
                color = self.hsv_to_rgb(hue, saturation, 0.8)
                
                self.canvas.create_rectangle(
                    band * band_width, y - bar_height * 0.1,
                    (band + 1) * band_width - 1, y,
                    fill=color, outline=color
                )


class FireEffect(VisualEffect):
    """火焰效果"""
    def draw(self):
        for x in range(0, self.width, 15):
            for y in range(self.height // 2, self.height, 15):
                energy = self.audio.get_band_energy(x % 64)
                dist = math.sqrt((x - self.center_x) ** 2 + (y - self.height) ** 2)
                intensity = max(0, 1 - dist / (self.width * 0.5))
                intensity *= (0.3 + energy * 0.7)
                
                hue = 0.05 - intensity * 0.03
                color = self.hsv_to_rgb(max(0, hue), 1.0, intensity)
                
                self.canvas.create_rectangle(x, y, x + 13, y + 13, fill=color, outline=color)


class FractalEffect(VisualEffect):
    """分形效果"""
    def draw(self):
        for i in range(6):
            angle = i * math.pi / 3 + self.time * 0.5
            length = 80 + self.audio.get_band_energy(i * 10) * 80
            
            x1 = self.center_x
            y1 = self.center_y
            
            for depth in range(5):
                x2 = x1 + math.cos(angle) * length * (0.6 ** depth)
                y2 = y1 + math.sin(angle) * length * (0.6 ** depth)
                
                hue = (i / 6 + depth * 0.1 + self.time * 0.1) % 1.0
                color = self.hsv_to_rgb(hue, 0.8, 0.8)
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3 - depth // 2)
                
                x1, y1 = x2, y2


class GeometricEffect(VisualEffect):
    """几何图案效果"""
    def draw(self):
        num_shapes = 8
        for i in range(num_shapes):
            angle = (i / num_shapes) * math.pi * 2 + self.time
            radius = 100 + self.audio.get_band_energy(i * 8) * 100
            energy = self.audio.get_band_energy(i * 8)
            
            x = self.center_x + math.cos(angle) * radius * 0.5
            y = self.center_y + math.sin(angle) * radius * 0.3
            
            size = 20 + energy * 30
            
            hue = (i / num_shapes + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.7, 0.8)
            
            if i % 3 == 0:
                self.canvas.create_rectangle(x - size, y - size, x + size, y + size, fill=color, outline=color)
            elif i % 3 == 1:
                self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline=color)
            else:
                points = [x, y - size, x + size, y + size, x - size, y + size]
                self.canvas.create_polygon(points, fill=color, outline=color)


class SonarEffect(VisualEffect):
    """声纳效果"""
    def draw(self):
        num_lines = 32
        for i in range(num_lines):
            angle = (i / num_lines) * math.pi * 2
            energy = self.audio.get_band_energy(i * 2)
            
            for dist in range(0, 200, 20):
                alpha = 1.0 - dist / 200
                length = 5 + energy * 20
                
                x1 = self.center_x + math.cos(angle) * dist
                y1 = self.center_y + math.sin(angle) * dist
                x2 = x1 + math.cos(angle + 0.1) * length
                y2 = y1 + math.sin(angle + 0.1) * length
                
                hue = (i / num_lines + dist / 200 + self.time * 0.1) % 1.0
                color = self.hsv_to_rgb(hue, 0.8, alpha * 0.8)
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)


class SpectrumRaysEffect(VisualEffect):
    """频谱射线效果"""
    def draw(self):
        num_rays = 48
        for i in range(num_rays):
            angle = (i / num_rays) * math.pi * 2 + self.time * 0.5
            energy = self.audio.get_band_energy(i % 64)
            
            inner_radius = 30
            outer_radius = 150 + energy * 150
            
            x1 = self.center_x + math.cos(angle) * inner_radius
            y1 = self.center_y + math.sin(angle) * inner_radius
            x2 = self.center_x + math.cos(angle) * outer_radius
            y2 = self.center_y + math.sin(angle) * outer_radius
            
            hue = (i / num_rays + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.9)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2 + energy * 3)


class HeartEffect(VisualEffect):
    """跳动的心效果"""
    def draw(self):
        beat = self.audio.get_beat()
        scale = 1.0 + beat * 0.3
        
        num_points = 50
        points = []
        for i in range(num_points):
            t = (i / num_points) * math.pi * 2
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            
            x = self.center_x + x * 8 * scale + self.audio.get_band_energy(i % 64) * 10
            y = self.center_y + y * 8 * scale
            points.extend([x, y])
        
        hue = 0.95 + beat * 0.05
        color = self.hsv_to_rgb(hue % 1.0, 0.8, 0.9)
        self.canvas.create_polygon(*points, fill=color, outline=color)


class StarfieldEffect(VisualEffect):
    """星域效果"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.stars = [[random.random() * width, random.random() * height, random.random() * 3 + 1] for _ in range(100)]
    
    def draw(self):
        for star in self.stars:
            x, y, speed = star
            energy = self.audio.get_band_energy(int(x % 64))
            
            brightness = 0.3 + energy * 0.7
            color = self.hsv_to_rgb(0.6, 0.2, brightness)
            
            size = speed + energy * 2
            self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline=color)
            
            star[1] = (star[1] + speed + energy * 5) % self.height
            if star[1] >= self.height - 1:
                star[0] = random.random() * self.width


class KaleidoscopeEffect(VisualEffect):
    """万花筒效果"""
    def draw(self):
        num_arms = 8
        for arm in range(num_arms):
            angle_offset = (arm / num_arms) * math.pi * 2
            energy = self.audio.get_band_energy(arm * 8)
            
            for i in range(20):
                dist = i * 15 + 10
                angle = angle_offset + self.time * 0.3 + i * 0.1
                
                x = self.center_x + math.cos(angle) * dist
                y = self.center_y + math.sin(angle) * dist
                
                hue = (arm / num_arms + i / 20 + self.time * 0.1) % 1.0
                color = self.hsv_to_rgb(hue, 0.8, 0.7 + energy * 0.3)
                size = 3 + energy * 5
                
                self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline=color)


class SpectrumWaveEffect(VisualEffect):
    """频谱波浪效果"""
    def draw(self):
        num_waves = 5
        for wave in range(num_waves):
            points = []
            for i in range(100):
                x = (i / 99) * self.width
                freq_idx = int((i / 99) * 64)
                energy = self.audio.get_band_energy(freq_idx)
                
                y = self.height * 0.5 + math.sin(i * 0.1 + self.time * 2 + wave) * (30 + energy * 50) - wave * 20
                points.extend([x, y])
            
            hue = (wave / num_waves + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.7, 0.8)
            self.canvas.create_line(*points, fill=color, width=2)


class Cube3DEffect(VisualEffect):
    """3D立方体效果"""
    def draw(self):
        size = 80 + self.audio.get_band_energy(0) * 50
        angle = self.time * 0.5
        
        vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        
        def rotate_3d(x, y, z):
            x_rot = x * math.cos(angle) - z * math.sin(angle)
            z_rot = x * math.sin(angle) + z * math.cos(angle)
            y_rot = y * math.cos(angle * 0.7) - z_rot * math.sin(angle * 0.7)
            z_rot = y * math.sin(angle * 0.7) + z_rot * math.cos(angle * 0.7)
            return x_rot * size + self.center_x, y_rot * size + self.center_y
        
        edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
        
        for i, (a, b) in enumerate(edges):
            v1 = vertices[a]
            v2 = vertices[b]
            x1, y1 = rotate_3d(*v1)
            x2, y2 = rotate_3d(*v2)
            
            hue = (i / len(edges) + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.9)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)


class CellularAutomatonEffect(VisualEffect):
    """元胞自动机效果 - 音频驱动的生命游戏"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.cell_size = 10
        self.cols = width // self.cell_size
        self.rows = height // self.cell_size
        self.grid = [[random.random() > 0.7 for _ in range(self.cols)] for _ in range(self.rows)]
        self.age_grid = [[0] * self.cols for _ in range(self.rows)]
        self.update_counter = 0
        self.update_interval = 3
    
    def count_neighbors(self, x, y):
        """计算活着的邻居数量"""
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                nx = (x + i) % self.cols
                ny = (y + j) % self.rows
                if self.grid[ny][nx]:
                    count += 1
        return count
    
    def update(self, dt):
        super().update(dt)
        self.update_counter += 1
        
        energy = self.audio.get_band_energy(int(self.time * 10) % 64)
        self.update_interval = max(1, int(5 - energy * 4))
        
        if self.update_counter >= self.update_interval:
            self.update_counter = 0
            self.evolve_grid(energy)
    
    def evolve_grid(self, energy):
        """根据元胞自动机规则更新网格"""
        new_grid = [[False] * self.cols for _ in range(self.rows)]
        new_age = [[0] * self.cols for _ in range(self.rows)]
        
        for y in range(self.rows):
            for x in range(self.cols):
                neighbors = self.count_neighbors(x, y)
                alive = self.grid[y][x]
                
                birth_probability = 0.05 + energy * 0.15
                
                if alive:
                    new_grid[y][x] = 2 <= neighbors <= 3
                    new_age[y][x] = self.age_grid[y][x] + 1 if new_grid[y][x] else 0
                else:
                    new_grid[y][x] = random.random() < birth_probability
                    if new_grid[y][x]:
                        new_age[y][x] = 1
        
        self.grid = new_grid
        self.age_grid = new_age
    
    def draw(self):
        max_age = 20
        
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x]:
                    age = min(self.age_grid[y][x], max_age)
                    age_ratio = age / max_age
                    
                    hue = (0.35 + age_ratio * 0.15) % 1.0
                    saturation = 0.9
                    brightness = 0.4 + age_ratio * 0.6
                    
                    color = self.hsv_to_rgb(hue, saturation, brightness)
                    
                    px = x * self.cell_size
                    py = y * self.cell_size
                    
                    self.canvas.create_rectangle(
                        px, py, 
                        px + self.cell_size - 1, 
                        py + self.cell_size - 1,
                        fill=color, outline=color
                    )
                
                elif random.random() < 0.001:
                    energy = self.audio.get_band_energy((x + y) % 64)
                    if energy > 0.3:
                        hue = (self.time * 0.1 + energy) % 1.0
                        color = self.hsv_to_rgb(hue, 0.8, 0.3)
                        
                        px = x * self.cell_size
                        py = y * self.cell_size
                        
                        self.canvas.create_rectangle(
                            px, py,
                            px + self.cell_size - 1,
                            py + self.cell_size - 1,
                            fill=color, outline=color
                        )


# ==================== 扩展可视化效果 ====================

class RingPulseEffect(VisualEffect):
    """环形脉冲效果 - 中心向外扩散的同心圆环"""
    def draw(self):
        num_rings = 8
        beat = self.audio.get_beat()
        
        for i in range(num_rings):
            phase = (i / num_rings + self.time * 0.5) % 1.0
            base_radius = 30 + i * 25
            energy = self.audio.get_band_energy(i * 8)
            
            radius = base_radius + energy * 80 + beat * 30
            alpha = max(0.2, 1.0 - i / num_rings - energy * 0.3)
            
            hue = (i / num_rings + self.time * 0.1) % 1.0
            saturation = 0.7
            brightness = alpha * 0.8
            
            color = self.hsv_to_rgb(hue, saturation, brightness)
            
            self.canvas.create_oval(
                self.center_x - radius, self.center_y - radius,
                self.center_x + radius, self.center_y + radius,
                outline=color, width=2 + int(energy * 3)
            )


class PolarGridEffect(VisualEffect):
    """极坐标网格效果 - 基于极坐标系的网格线"""
    def draw(self):
        num_rings = 10
        num_lines = 24
        beat = self.audio.get_beat()
        
        for i in range(num_rings):
            radius = 20 + i * 25
            energy = self.audio.get_band_energy(i * 6)
            pulse = 1.0 + energy * 0.5 + beat * 0.3
            
            hue = (i / num_rings + self.time * 0.05) % 1.0
            color = self.hsv_to_rgb(hue, 0.6, 0.7)
            
            self.canvas.create_oval(
                self.center_x - radius * pulse, self.center_y - radius * pulse,
                self.center_x + radius * pulse, self.center_y + radius * pulse,
                outline=color, width=1
            )
        
        for i in range(num_lines):
            angle = (i / num_lines) * math.pi * 2 + self.time * 0.2
            energy = self.audio.get_band_energy(i * 3)
            length = 200 + energy * 100
            
            x = self.center_x + math.cos(angle) * length
            y = self.center_y + math.sin(angle) * length
            
            hue = (i / num_lines + 0.5 + self.time * 0.05) % 1.0
            color = self.hsv_to_rgb(hue, 0.6, 0.6)
            
            self.canvas.create_line(self.center_x, self.center_y, x, y, fill=color, width=1)


class ParticleBurstEffect(VisualEffect):
    """粒子爆发效果 - 从中心爆发向外扩散的粒子群"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.particles = []
        self.max_particles = 150
        
    def update(self, dt):
        super().update(dt)
        beat = self.audio.get_beat()
        energy = self.audio.get_band_energy(int(self.time * 20) % 64)
        
        if beat > 0.5 or energy > 0.4:
            for _ in range(int(5 + energy * 15)):
                angle = random.uniform(0, math.pi * 2)
                speed = 2 + random.uniform(0, 5) + energy * 8
                self.particles.append({
                    'x': self.center_x,
                    'y': self.center_y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': 1.0,
                    'hue': random.random()
                })
        
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.02
            p['vx'] *= 0.98
            p['vy'] *= 0.98
            
            if p['life'] <= 0:
                self.particles.remove(p)
        
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def draw(self):
        for p in self.particles:
            size = 2 + p['life'] * 4
            color = self.hsv_to_rgb(p['hue'], 0.8, p['life'])
            self.canvas.create_oval(
                p['x'] - size, p['y'] - size,
                p['x'] + size, p['y'] + size,
                fill=color, outline=color
            )


class AudioFingerprintEffect(VisualEffect):
    """音频指纹效果 - 音频频谱的轮廓线"""
    def draw(self):
        points_top = []
        points_bottom = []
        
        for i in range(80):
            x = (i / 79) * self.width
            freq_idx = int((i / 79) * 64)
            energy = self.audio.get_band_energy(freq_idx)
            
            amplitude = 80 + energy * 120
            y_top = self.center_y - amplitude
            y_bottom = self.center_y + amplitude
            
            points_top.extend([x, y_top])
            points_bottom.extend([x, y_bottom])
        
        hue = self.time * 0.1 % 1.0
        color = self.hsv_to_rgb(hue, 0.8, 0.9)
        self.canvas.create_line(*points_top, fill=color, width=2)
        
        color2 = self.hsv_to_rgb((hue + 0.5) % 1.0, 0.8, 0.9)
        self.canvas.create_line(*points_bottom, fill=color2, width=2)
        
        for i in range(0, 80, 4):
            x = (i / 79) * self.width
            freq_idx = int((i / 79) * 64)
            energy = self.audio.get_band_energy(freq_idx)
            
            y1 = self.center_y - (80 + energy * 120)
            y2 = self.center_y + (80 + energy * 120)
            
            self.canvas.create_line(x, y1, x, y2, fill=color, width=1)


class SpectrumMountainEffect(VisualEffect):
    """频谱山峦效果 - 3D视角的频谱柱状图"""
    def draw(self):
        num_bars = 40
        bar_width = self.width / num_bars
        depth = 15
        
        for layer in range(depth, -1, -1):
            layer_alpha = 0.3 + (1 - layer / depth) * 0.5
            layer_offset = layer * 5
            
            for i in range(num_bars):
                x = i * bar_width
                freq_idx = int((i / num_bars) * 64)
                energy = self.audio.get_band_energy(freq_idx)
                
                bar_height = energy * self.height * 0.6
                
                hue = (i / num_bars + self.time * 0.05) % 1.0
                saturation = 0.7
                brightness = layer_alpha * (0.5 + energy * 0.5)
                
                color = self.hsv_to_rgb(hue, saturation, brightness)
                
                y_top = self.height - bar_height + layer_offset
                y_bottom = self.height + layer_offset
                
                self.canvas.create_rectangle(
                    x, y_top, x + bar_width - 1, y_bottom,
                    fill=color, outline=color
                )


class CircularSpectrumEffect(VisualEffect):
    """环形频谱效果 - 将频谱数据映射到圆环上"""
    def draw(self):
        num_points = 72
        
        for ring in range(4):
            points = []
            ring_radius = 60 + ring * 35
            base_hue = ring * 0.15
            
            for i in range(num_points):
                angle = (i / num_points) * math.pi * 2
                freq_idx = int(i * 64 / num_points)
                energy = self.audio.get_band_energy(freq_idx)
                
                r = ring_radius + energy * 40
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.extend([x, y])
            
            hue = (base_hue + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.7, 0.8 - ring * 0.15)
            
            self.canvas.create_line(*points, fill=color, width=2)


class DNAHelixEffect(VisualEffect):
    """DNA螺旋效果 - 双螺旋结构随音频旋转和振动"""
    def draw(self):
        num_points = 40
        amplitude = 60 + self.audio.get_band_energy(0) * 40
        frequency = 3
        twist = self.time * 2
        
        points1 = []
        points2 = []
        
        for i in range(num_points):
            y = (i / (num_points - 1)) * self.height
            phase = i / num_points * math.pi * 2 * frequency + twist
            
            energy1 = self.audio.get_band_energy(i % 64)
            energy2 = self.audio.get_band_energy((i + 32) % 64)
            
            x1 = self.center_x + math.sin(phase) * amplitude * (1 + energy1 * 0.5)
            x2 = self.center_x - math.sin(phase) * amplitude * (1 + energy2 * 0.5)
            
            points1.extend([x1, y])
            points2.extend([x2, y])
            
            if i > 0:
                hue1 = (i / num_points + self.time * 0.1) % 1.0
                hue2 = (i / num_points + 0.5 + self.time * 0.1) % 1.0
                
                color1 = self.hsv_to_rgb(hue1, 0.8, 0.7 + energy1 * 0.3)
                color2 = self.hsv_to_rgb(hue2, 0.8, 0.7 + energy2 * 0.3)
                
                self.canvas.create_line(
                    points1[-4], points1[-3], x1, y,
                    fill=color1, width=2 + int(energy1 * 3)
                )
                self.canvas.create_line(
                    points2[-4], points2[-3], x2, y,
                    fill=color2, width=2 + int(energy2 * 3)
                )
                
                if i % 5 == 0:
                    self.canvas.create_line(x1, y, x2, y, fill='#444444', width=1)


class NoteRainEffect(VisualEffect):
    """音符雨效果 - 下落的音符符号，大小随能量变化"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.notes = []
        self.note_chars = "♪♫♬♩♭♮♪♫"
    
    def update(self, dt):
        super().update(dt)
        energy = self.audio.get_band_energy(int(self.time * 10) % 64)
        
        if energy > 0.2:
            x = random.uniform(0, self.width)
            self.notes.append({
                'x': x,
                'y': 0,
                'char': random.choice(self.note_chars),
                'speed': 2 + energy * 8,
                'hue': random.random(),
                'size': 12 + energy * 16
            })
        
        for note in self.notes[:]:
            note['y'] += note['speed']
            if note['y'] > self.height:
                self.notes.remove(note)
    
    def draw(self):
        for note in self.notes:
            energy = self.audio.get_band_energy(int(note['x']) % 64)
            color = self.hsv_to_rgb(note['hue'], 0.7, 0.6 + energy * 0.4)
            self.canvas.create_text(
                note['x'], note['y'],
                text=note['char'],
                fill=color,
                font=("Arial", int(note['size']))
            )


class SoundVortexEffect(VisualEffect):
    """声音漩涡效果 - 3D效果的漩涡隧道"""
    def draw(self):
        num_layers = 12
        num_points = 24
        
        for layer in range(num_layers):
            z = layer / num_layers
            scale = 0.3 + z * 0.7
            alpha = 1.0 - z * 0.7
            
            points = []
            for i in range(num_points):
                angle = (i / num_points) * math.pi * 2 + self.time * (2 - z) + z * math.pi
                energy = self.audio.get_band_energy((i + layer * 5) % 64)
                
                radius = 30 + energy * 60
                x = self.center_x + math.cos(angle) * radius * scale
                y = self.center_y + math.sin(angle) * radius * scale * 0.6
                
                points.extend([x, y])
            
            hue = (layer / num_layers + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, alpha * 0.8)
            
            self.canvas.create_line(*points, fill=color, width=2)


class NeonTunnelEffect(VisualEffect):
    """霓虹隧道效果 - 向内延伸的彩色隧道"""
    def draw(self):
        num_layers = 15
        num_segments = 16
        
        for i in range(num_layers):
            depth = i / num_layers
            scale = (1 - depth) * 0.8 + 0.2
            alpha = 1.0 - depth * 0.8
            
            energy = self.audio.get_band_energy(i * 4 % 64)
            radius = 50 + energy * 100
            
            points = []
            for j in range(num_segments):
                angle = (j / num_segments) * math.pi * 2 + self.time * (1 - depth * 0.5)
                x = self.center_x + math.cos(angle) * radius * scale
                y = self.center_y + math.sin(angle) * radius * scale
                points.extend([x, y])
            
            hue = (i / num_layers + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.9, alpha * 0.9)
            
            self.canvas.create_line(*points, fill=color, width=2 + int(energy * 2))


class RippleEffect(VisualEffect):
    """水波涟漪效果 - 模拟水滴落入水面产生的涟漪"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.ripples = []
    
    def update(self, dt):
        super().update(dt)
        beat = self.audio.get_beat()
        energy = self.audio.get_band_energy(int(self.time * 15) % 64)
        
        if beat > 0.3 or energy > 0.5:
            x = self.center_x + random.uniform(-100, 100)
            y = self.center_y + random.uniform(-100, 100)
            self.ripples.append({
                'x': x, 'y': y,
                'radius': 5,
                'max_radius': 50 + energy * 100,
                'life': 1.0,
                'hue': random.random()
            })
        
        for ripple in self.ripples[:]:
            ripple['radius'] += 2
            ripple['life'] -= 0.02
            
            if ripple['radius'] >= ripple['max_radius'] or ripple['life'] <= 0:
                self.ripples.remove(ripple)
    
    def draw(self):
        for ripple in self.ripples:
            color = self.hsv_to_rgb(ripple['hue'], 0.6, ripple['life'] * 0.8)
            self.canvas.create_oval(
                ripple['x'] - ripple['radius'], ripple['y'] - ripple['radius'] * 0.5,
                ripple['x'] + ripple['radius'], ripple['y'] + ripple['radius'] * 0.5,
                outline=color, width=2
            )


class MobiusStripEffect(VisualEffect):
    """3D旋转环效果 - 3D旋转的莫比乌斯带"""
    def draw(self):
        num_points = 50
        num_loops = 2
        energy = self.audio.get_band_energy(0)
        
        angle = self.time * 0.8
        
        for i in range(num_points):
            t = (i / num_points) * math.pi * 2
            
            for loop in range(num_loops):
                u = t + loop * math.pi
                
                x_3d = math.cos(u) * (1 + math.cos(t) / 2)
                y_3d = math.sin(u) * (1 + math.cos(t) / 2)
                z_3d = math.sin(t) / 2
                
                x_rot = x_3d * math.cos(angle) - z_3d * math.sin(angle)
                z_rot = x_3d * math.sin(angle) + z_3d * math.cos(angle)
                y_rot = y_3d * math.cos(angle * 0.7) - z_rot * math.sin(angle * 0.7)
                
                scale = 60 + energy * 40
                x = self.center_x + x_rot * scale
                y = self.center_y + y_rot * scale
                
                hue = (i / num_points + loop / num_loops + self.time * 0.1) % 1.0
                color = self.hsv_to_rgb(hue, 0.8, 0.8)
                
                if i > 0:
                    self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)


class FractalTreeEffect(VisualEffect):
    """分形树效果 - 递归分形树随音频摇摆"""
    def draw_branch(self, x, y, length, angle, depth, hue_offset):
        if depth == 0 or length < 3:
            return
        
        energy = self.audio.get_band_energy((depth * 10 + int(angle)) % 64)
        sway = math.sin(self.time * 2 + depth * 0.5) * (10 - depth) * 0.5
        
        x2 = x + math.cos(angle + sway * 0.02) * length
        y2 = y + math.sin(angle + sway * 0.02) * length
        
        hue = (hue_offset + depth * 0.05 + self.time * 0.1) % 1.0
        color = self.hsv_to_rgb(hue, 0.7, 0.4 + depth * 0.05)
        
        self.canvas.create_line(x, y, x2, y2, fill=color, width=max(1, depth // 3))
        
        branch_angle = 0.4 + energy * 0.3
        self.draw_branch(x2, y2, length * 0.7, angle - branch_angle, depth - 1, hue_offset)
        self.draw_branch(x2, y2, length * 0.7, angle + branch_angle, depth - 1, hue_offset)
    
    def draw(self):
        energy = self.audio.get_band_energy(0)
        depth = 8 + int(energy * 4)
        
        self.draw_branch(
            self.center_x, self.height,
            60 + energy * 40,
            -math.pi / 2,
            depth,
            0.3
        )


class HyperCubeEffect(VisualEffect):
    """超立方体效果 - 4D超立方体的3D投影"""
    def project_4d(self, x, y, z, w, angle_w):
        x4 = x * math.cos(angle_w) - w * math.sin(angle_w)
        w4 = x * math.sin(angle_w) + w * math.cos(angle_w)
        
        y4 = y * math.cos(angle_w * 0.7) - z * math.sin(angle_w * 0.7)
        z4 = y * math.sin(angle_w * 0.7) + z * math.cos(angle_w * 0.7)
        
        return x4, y4, z4, w4
    
    def draw(self):
        size = 50 + self.audio.get_band_energy(0) * 30
        angle = self.time * 0.5
        angle2 = self.time * 0.3
        
        vertices = []
        for i in range(16):
            v = [
                (i & 1) * 2 - 1,
                (i >> 1 & 1) * 2 - 1,
                (i >> 2 & 1) * 2 - 1,
                (i >> 3 & 1) * 2 - 1
            ]
            
            x, y, z, w = self.project_4d(v[0] * size, v[1] * size, v[2] * size, v[3] * size, angle)
            
            x_3d = x * math.cos(angle2) - z * math.sin(angle2)
            z_3d = x * math.sin(angle2) + z * math.cos(angle2)
            y_3d = y * math.cos(angle2 * 0.5) - w * math.sin(angle2 * 0.5)
            w_3d = y * math.sin(angle2 * 0.5) + w * math.cos(angle2 * 0.5)
            
            px = self.center_x + x_3d * 0.8 + w_3d * 0.3
            py = self.center_y + y_3d * 0.8 - w_3d * 0.3
            
            vertices.append((px, py))
        
        edges = [
            (0,1), (1,3), (3,2), (2,0),
            (4,5), (5,7), (7,6), (6,4),
            (0,4), (1,5), (2,6), (3,7),
            (8,9), (9,11), (11,10), (10,8),
            (12,13), (13,15), (15,14), (14,12),
            (8,12), (9,13), (10,14), (11,15),
            (0,8), (1,9), (2,10), (3,11),
            (4,12), (5,13), (6,14), (7,15)
        ]
        
        for i, (a, b) in enumerate(edges):
            x1, y1 = vertices[a]
            x2, y2 = vertices[b]
            
            hue = (i / len(edges) + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 0.9)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)


class GradientWallEffect(VisualEffect):
    """频谱渐变墙效果 - 左右渐变的彩色墙面"""
    def draw(self):
        num_bands = 64
        
        for i in range(num_bands):
            energy = self.audio.get_band_energy(i)
            
            height = self.height * (0.3 + energy * 0.7)
            y = self.height - height
            
            hue1 = (i / num_bands + self.time * 0.05) % 1.0
            hue2 = (i / num_bands + 0.1 + self.time * 0.05) % 1.0
            
            color1 = self.hsv_to_rgb(hue1, 0.8, 0.6 + energy * 0.4)
            color2 = self.hsv_to_rgb(hue2, 0.8, 0.6 + energy * 0.4)
            
            x = (i / num_bands) * self.width
            
            self.canvas.create_rectangle(
                x, y, x + self.width / num_bands, self.height,
                fill=color1, outline=color1
            )
            
            self.canvas.create_rectangle(
                x, y, x + self.width / num_bands / 2, self.height,
                fill=color2, outline=color2
            )


class AuroraEffect(VisualEffect):
    """极光效果 - 北极光般的流动光效"""
    def draw(self):
        num_curves = 8
        
        for i in range(num_curves):
            points = []
            base_y = self.height * 0.3 + i * 30
            
            for x in range(0, self.width, 15):
                energy = self.audio.get_band_energy(int(x / self.width * 64))
                wave = math.sin(x * 0.02 + self.time * 2 + i) * 30
                wave2 = math.sin(x * 0.01 + self.time + i * 0.5) * 20
                y = base_y + wave + wave2 + energy * 50
                
                points.extend([x, y])
            
            hue = (i / num_curves + 0.5 + self.time * 0.05) % 1.0
            color = self.hsv_to_rgb(hue, 0.6, 0.4 + i * 0.05)
            
            width = 4 + i // 2
            self.canvas.create_line(*points, fill=color, width=width)


class StarTwinkleEffect(VisualEffect):
    """星光闪烁效果 - 随机闪烁的星星群"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.stars = [[random.random() * width, random.random() * height * 0.8,
                       random.random() * 2 + 1, random.random()] for _ in range(200)]
    
    def draw(self):
        energy = self.audio.get_band_energy(int(self.time * 5) % 64)
        
        for star in self.stars:
            x, y, base_size, base_hue = star
            
            twinkle = math.sin(self.time * 3 + x * 0.1) * 0.3 + 0.7
            brightness = twinkle * (0.3 + energy * 0.7)
            
            size = base_size * (1 + energy * 2)
            
            hue = (base_hue + energy * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.3, brightness)
            
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=color
            )


class BouncingBallsEffect(VisualEffect):
    """音频弹跳球效果 - 物理模拟的弹跳球"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.balls = []
        self.gravity = 0.3
        self.damping = 0.85
        
        for _ in range(15):
            self.balls.append({
                'x': random.uniform(50, width - 50),
                'y': random.uniform(50, height // 2),
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'radius': random.uniform(10, 25),
                'hue': random.random()
            })
    
    def update(self, dt):
        super().update(dt)
        beat = self.audio.get_beat()
        energy = self.audio.get_band_energy(int(self.time * 10) % 64)
        
        if beat > 0.5:
            for ball in self.balls:
                ball['vy'] -= beat * 10
        
        for ball in self.balls:
            ball['vy'] += self.gravity
            ball['x'] += ball['vx']
            ball['y'] += ball['vy']
            
            if ball['y'] + ball['radius'] > self.height:
                ball['y'] = self.height - ball['radius']
                ball['vy'] *= -self.damping
            
            if ball['x'] - ball['radius'] < 0:
                ball['x'] = ball['radius']
                ball['vx'] *= -self.damping
            elif ball['x'] + ball['radius'] > self.width:
                ball['x'] = self.width - ball['radius']
                ball['vx'] *= -self.damping
    
    def draw(self):
        for ball in self.balls:
            energy = self.audio.get_band_energy(int(ball['x']) % 64)
            color = self.hsv_to_rgb(ball['hue'], 0.8, 0.5 + energy * 0.5)
            
            self.canvas.create_oval(
                ball['x'] - ball['radius'], ball['y'] - ball['radius'],
                ball['x'] + ball['radius'], ball['y'] + ball['radius'],
                fill=color, outline=color
            )


class ParticleConnectEffect(VisualEffect):
    """粒子连线效果 - 随机粒子间根据距离连线"""
    def __init__(self, canvas, width, height, audio_sim):
        super().__init__(canvas, width, height, audio_sim)
        self.particles = []
        for _ in range(40):
            self.particles.append({
                'x': random.random() * width,
                'y': random.random() * height,
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'hue': random.random()
            })
    
    def update(self, dt):
        super().update(dt)
        energy = self.audio.get_band_energy(int(self.time * 10) % 64)
        
        for p in self.particles:
            p['x'] += p['vx'] * (1 + energy * 3)
            p['y'] += p['vy'] * (1 + energy * 3)
            
            if p['x'] < 0 or p['x'] > self.width:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > self.height:
                p['vy'] *= -1
            
            p['x'] = max(0, min(self.width, p['x']))
            p['y'] = max(0, min(self.height, p['y']))
    
    def draw(self):
        max_dist = 100 + self.audio.get_band_energy(0) * 50
        
        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i+1:]:
                dx = p1['x'] - p2['x']
                dy = p1['y'] - p2['y']
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < max_dist:
                    alpha = 1.0 - dist / max_dist
                    hue = (p1['hue'] + p2['hue']) / 2
                    color = self.hsv_to_rgb(hue, 0.6, alpha * 0.7)
                    
                    self.canvas.create_line(p1['x'], p1['y'], p2['x'], p2['y'],
                                          fill=color, width=1)


class MouseFollowerEffect(VisualEffect):
    """鼠标跟随效果 - 跟随鼠标的粒子和光效"""
    def __init__(self, canvas, width, height, audio_sim, mouse_pos=None):
        super().__init__(canvas, width, height, audio_sim)
        self.mouse_pos = mouse_pos
        self.particles = []
        self.max_particles = 100
        self.trail_length = 20
        self.ripples = []
        self.arrow_trail = []
        self.arrow_color_hue = 0.0
        
    def update(self, dt):
        super().update(dt)
        self.arrow_color_hue = (self.arrow_color_hue + 0.02) % 1.0
        
        for ripple in self.ripples[:]:
            ripple['radius'] += 3
            ripple['life'] -= 0.03
            
            if ripple['life'] <= 0:
                self.ripples.remove(ripple)
        
        if self.mouse_pos and self.mouse_pos[0] is not None:
            mx, my = self.mouse_pos
            
            for _ in range(3):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(5, 20)
                self.particles.append({
                    'x': mx + math.cos(angle) * dist,
                    'y': my + math.sin(angle) * dist,
                    'vx': math.cos(angle) * random.uniform(1, 3),
                    'vy': math.sin(angle) * random.uniform(1, 3),
                    'life': 1.0,
                    'size': random.uniform(2, 6),
                    'hue': random.random()
                })
            
            self.arrow_trail.append({
                'x': mx,
                'y': my,
                'life': 1.0
            })
            
            if len(self.arrow_trail) > self.trail_length:
                self.arrow_trail.pop(0)
        
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.025
            p['vx'] *= 0.95
            p['vy'] *= 0.95
            
            if p['life'] <= 0:
                self.particles.remove(p)
        
        for trail in self.arrow_trail[:]:
            trail['life'] -= 0.05
            if trail['life'] <= 0:
                self.arrow_trail.remove(trail)
        
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def draw(self):
        for ripple in self.ripples:
            color = self.hsv_to_rgb(ripple['hue'], 0.6, ripple['life'])
            self.canvas.create_oval(
                ripple['x'] - ripple['radius'], ripple['y'] - ripple['radius'],
                ripple['x'] + ripple['radius'], ripple['y'] + ripple['radius'],
                outline=color, width=2
            )
        
        for i, trail in enumerate(self.arrow_trail):
            alpha = trail['life']
            hue = (self.arrow_color_hue + i / len(self.arrow_trail)) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, alpha)
            
            size = 3 + alpha * 5
            self.canvas.create_oval(
                trail['x'] - size, trail['y'] - size,
                trail['x'] + size, trail['y'] + size,
                fill=color, outline=color
            )
        
        for p in self.particles:
            size = p['size'] * p['life']
            color = self.hsv_to_rgb(p['hue'], 0.8, p['life'])
            self.canvas.create_oval(
                p['x'] - size, p['y'] - size,
                p['x'] + size, p['y'] + size,
                fill=color, outline=color
            )
        
        if self.mouse_pos and self.mouse_pos[0] is not None:
            mx, my = self.mouse_pos
            energy = self.audio.get_band_energy(0)
            
            arrow_size = 15 + energy * 10
            color = self.hsv_to_rgb(self.arrow_color_hue, 0.9, 1.0)
            
            points = [
                mx, my - arrow_size,
                mx - arrow_size * 0.6, my + arrow_size * 0.5,
                mx, my,
                mx + arrow_size * 0.6, my + arrow_size * 0.5,
            ]
            self.canvas.create_polygon(points, fill=color, outline='white', width=1)
    
    def add_ripple(self, x, y):
        self.ripples.append({
            'x': x,
            'y': y,
            'radius': 5,
            'life': 1.0,
            'hue': random.random()
        })
    
    def set_mouse_pos(self, pos):
        self.mouse_pos = pos


# ==================== 新增效果 ====================
class SpectrumWaves3DEffect(VisualEffect):
    """3D频谱波浪"""
    def draw(self):
        num_waves = 8
        
        for wave in range(num_waves):
            points = []
            phase = wave * 0.5 + self.time
            
            for i in range(101):  # 101个点，包含起始和结束
                x = (i / 100.0) * self.width
                freq_idx = int((i / 100.0) * 64)
                energy = self.audio.get_band_energy(freq_idx)
                
                # 3D效果：每个波浪有不同的高度
                wave_height = math.sin(x * 0.02 + phase) * 30
                y = self.height * 0.7 + wave_height - wave * 10 + energy * 50
                
                points.append((x, y))
            
            # 绘制波浪线
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                hue = (wave / num_waves + self.time * 0.1) % 1.0
                color = self.hsv_to_rgb(hue, 0.8, 1.0)
                
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

class AudioMoireEffect(VisualEffect):
    """音频莫尔条纹"""
    def draw(self):
        lines_per_band = 3
        line_spacing = 20
        
        for band in range(32):
            energy = self.audio.get_band_energy(band)
            
            # 绘制水平条纹
            for i in range(lines_per_band):
                y = band * line_spacing + i * 5
                wave_height = math.sin(self.time + band * 0.1) * energy * 20
                
                for x in range(0, self.width, 20):
                    x1 = x
                    y1 = y + wave_height
                    x2 = x + 10
                    y2 = y + 10 + wave_height
                    
                    hue = (band / 32 + self.time * 0.05) % 1.0
                    color = self.hsv_to_rgb(hue, 0.8, 0.7)
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
            
            # 绘制垂直条纹
            for i in range(lines_per_band):
                x = band * line_spacing + i * 5
                wave_width = math.sin(self.time + band * 0.1) * energy * 20
                
                for y in range(0, self.height, 20):
                    x1 = x + wave_width
                    y1 = y
                    x2 = x + 10 + wave_width
                    y2 = y + 10
                    
                    hue = (band / 32 + self.time * 0.05 + 0.5) % 1.0
                    color = self.hsv_to_rgb(hue, 0.8, 0.7)
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

class SpectrumOrbEffect(VisualEffect):
    """频谱球体"""
    def draw(self):
        radius = 150
        num_points = 72
        
        for i in range(num_points):
            angle1 = (i / num_points) * math.pi * 2
            angle2 = ((i + 1) / num_points) * math.pi * 2
            
            # 计算球体上的点
            band_idx1 = int(i * 64 / num_points)
            band_idx2 = int((i + 1) * 64 / num_points)
            
            energy1 = self.audio.get_band_energy(band_idx1)
            energy2 = self.audio.get_band_energy(band_idx2)
            
            r1 = radius + energy1 * 50
            r2 = radius + energy2 * 50
            
            x1 = self.center_x + math.cos(angle1) * r1
            y1 = self.center_y + math.sin(angle1) * r1
            x2 = self.center_x + math.cos(angle2) * r2
            y2 = self.center_y + math.sin(angle2) * r2
            
            # 绘制球体线段
            hue = (i / num_points + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 1.0)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
        
        # 绘制中心
        center_color = self.hsv_to_rgb(self.time * 0.2, 0.9, 1.0)
        self.canvas.create_oval(
            self.center_x - 20, self.center_y - 20,
            self.center_x + 20, self.center_y + 20,
            fill=center_color, outline=center_color
        )

class AudioFlowerEffect(VisualEffect):
    """音频花朵"""
    def draw(self):
        num_petals = 12
        base_radius = 100
        
        points = []
        
        for i in range(num_petals * 2):
            angle = (i / (num_petals * 2)) * math.pi * 2
            band_idx = int(i * 32 / (num_petals * 2))
            energy = self.audio.get_band_energy(band_idx)
            
            # 花瓣形状
            t = i / 2.0
            r = base_radius + math.sin(angle * 2) * 30 + energy * 60
            
            x = self.center_x + math.cos(angle) * r
            y = self.center_y + math.sin(angle) * r
            
            points.append((x, y))
        
        # 绘制花朵
        fill_color = self.hsv_to_rgb(self.time * 0.1, 0.7, 0.6)
        outline_color = self.hsv_to_rgb(self.time * 0.1 + 0.5, 0.8, 1.0)
        
        if len(points) >= 3:
            coords = []
            for x, y in points:
                coords.extend([x, y])
            
            self.canvas.create_polygon(coords, fill=fill_color, outline=outline_color, width=2)
        
        # 绘制花蕊
        for i in range(8):
            angle = (i / 8) * math.pi * 2 + self.time
            radius = 20 + math.sin(self.time * 2) * 5
            
            x = self.center_x + math.cos(angle) * radius
            y = self.center_y + math.sin(angle) * radius
            
            dot_color = self.hsv_to_rgb(i / 8 + self.time * 0.2, 0.9, 1.0)
            dot_size = 5 + math.sin(self.time + i) * 3
            
            self.canvas.create_oval(
                x - dot_size, y - dot_size,
                x + dot_size, y + dot_size,
                fill=dot_color, outline=dot_color
            )

class SpectrumSpiralEffect(VisualEffect):
    """频谱螺旋"""
    def draw(self):
        num_turns = 6
        points_per_turn = 100
        max_radius = 250
        
        points = []
        
        for i in range(num_turns * points_per_turn):
            progress = i / (num_turns * points_per_turn)
            angle = progress * math.pi * 2 * num_turns + self.time
            radius = progress * max_radius
            
            band_idx = int(progress * 64)
            energy = self.audio.get_band_energy(band_idx)
            
            # 根据音频能量调整半径
            radius += energy * 50
            
            x = self.center_x + math.cos(angle) * radius
            y = self.center_y + math.sin(angle) * radius
            
            points.append((x, y))
        
        # 绘制螺旋线
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            hue = (i / len(points) + self.time * 0.1) % 1.0
            color = self.hsv_to_rgb(hue, 0.8, 1.0)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1)
        
        # 绘制螺旋中心
        center_color = self.hsv_to_rgb(self.time * 0.2, 0.9, 1.0)
        center_size = 10 + math.sin(self.time * 2) * 5
        
        self.canvas.create_oval(
            self.center_x - center_size, self.center_y - center_size,
            self.center_x + center_size, self.center_y + center_size,
            fill=center_color, outline=center_color
        )

class AudioGridEffect(VisualEffect):
    """音频网格"""
    def draw(self):
        cell_size = 30
        cols = self.width // cell_size
        rows = self.height // cell_size
        
        for col in range(cols + 1):
            for row in range(rows + 1):
                x = col * cell_size
                y = row * cell_size
                
                # 计算对应频带
                band_x = int((col / cols) * 32) if cols > 0 else 0
                band_y = int((row / rows) * 32) if rows > 0 else 0
                
                energy_x = self.audio.get_band_energy(band_x)
                energy_y = self.audio.get_band_energy(band_y)
                
                # 计算网格点变形
                dx = math.sin(self.time + col * 0.1) * energy_x * 15
                dy = math.sin(self.time + row * 0.1) * energy_y * 15
                
                x1 = x + dx
                y1 = y + dy
                
                # 绘制垂直线
                if col < cols:
                    band_next_x = int(((col + 1) / cols) * 32) if cols > 0 else 0
                    energy_next_x = self.audio.get_band_energy(band_next_x)
                    dx2 = math.sin(self.time + (col + 1) * 0.1) * energy_next_x * 15
                    
                    x2 = (col + 1) * cell_size + dx2
                    y2 = y1
                    
                    hue = (col / cols + self.time * 0.05) % 1.0
                    color = self.hsv_to_rgb(hue, 0.8, 0.7)
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1)
                
                # 绘制水平线
                if row < rows:
                    band_next_y = int(((row + 1) / rows) * 32) if rows > 0 else 0
                    energy_next_y = self.audio.get_band_energy(band_next_y)
                    dy2 = math.sin(self.time + (row + 1) * 0.1) * energy_next_y * 15
                    
                    x2 = x1
                    y2 = (row + 1) * cell_size + dy2
                    
                    hue = (row / rows + self.time * 0.05 + 0.3) % 1.0
                    color = self.hsv_to_rgb(hue, 0.8, 0.7)
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1)
                
                # 绘制网格点
                if col < cols and row < rows:
                    point_color = self.hsv_to_rgb(
                        (col + row) / (cols + rows) + self.time * 0.1, 0.9, 1.0
                    )
                    point_size = 2 + (energy_x + energy_y) * 3
                    
                    self.canvas.create_oval(
                        x1 - point_size, y1 - point_size,
                        x1 + point_size, y1 + point_size,
                        fill=point_color, outline=point_color
                    )

class SpectrumRipplesEffect(VisualEffect):
    """频谱涟漪"""
    def draw(self):
        num_circles = 10
        
        for i in range(num_circles):
            # 计算涟漪半径
            progress = (self.time + i * 0.3) % 1.0
            radius = 20 + progress * 200
            
            if progress < 0.8:
                # 计算对应频带的能量
                band_idx = int(progress * 32)
                energy = self.audio.get_band_energy(band_idx)
                
                # 涟漪透明度
                alpha = 1.0 - progress / 0.8
                
                # 计算颜色
                hue = (i / num_circles + self.time * 0.1) % 1.0
                r, g, b = self.hsv_to_rgb_components(hue, 0.8, alpha)
                color = f'#{r:02x}{g:02x}{b:02x}'
                
                # 绘制涟漪
                self.canvas.create_oval(
                    self.center_x - radius, self.center_y - radius,
                    self.center_x + radius, self.center_y + radius,
                    outline=color, width=1 + energy * 3
                )
    
    def hsv_to_rgb_components(self, h, s, v):
        """HSV转RGB，返回RGB分量"""
        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return int(r*255), int(g*255), int(b*255)

class AudioMazeEffect(VisualEffect):
    """音频迷宫"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cell_size = 20
        self.cols = self.width // self.cell_size
        self.rows = self.height // self.cell_size
        self.maze = [[0] * self.cols for _ in range(self.rows)]
        self.generate_maze()
        self.path = []
        self.path_index = 0
        self.path_progress = 0.0
    
    def generate_maze(self):
        """生成简单迷宫"""
        # 简单网格，有一些随机墙
        for y in range(self.rows):
            for x in range(self.cols):
                # 边界
                if x == 0 or y == 0 or x == self.cols-1 or y == self.rows-1:
                    self.maze[y][x] = 1
                # 随机墙
                elif random.random() < 0.2:
                    self.maze[y][x] = 1
                else:
                    self.maze[y][x] = 0
        
        # 确保入口和出口
        self.maze[1][0] = 0
        self.maze[self.rows-2][self.cols-1] = 0
    
    def update(self, dt):
        super().update(dt)
        
        # 更新路径进度
        beat = self.audio.get_beat()
        self.path_progress += dt * 0.2 + beat * 0.1
        
        if self.path_progress >= 1.0:
            self.path_progress = 0.0
            self.generate_maze()
            self.generate_path()
    
    def generate_path(self):
        """生成从入口到出口的路径"""
        self.path = []
        # 简单直线路径
        for y in range(1, self.rows-1):
            x = 1
            if self.maze[y][x] == 0:
                self.path.append((x, y))
        
        for x in range(1, self.cols-1):
            y = self.rows-2
            if self.maze[y][x] == 0:
                self.path.append((x, y))
    
    def draw(self):
        # 绘制迷宫墙
        for y in range(self.rows):
            for x in range(self.cols):
                if self.maze[y][x] == 1:
                    x1 = x * self.cell_size
                    y1 = y * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    
                    hue = ((x + y) / (self.cols + self.rows) + self.time * 0.05) % 1.0
                    color = self.hsv_to_rgb(hue, 0.8, 0.4)
                    
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
        
        # 绘制路径
        if self.path:
            path_index = int(self.path_progress * len(self.path))
            for i in range(min(path_index + 1, len(self.path))):
                x, y = self.path[i]
                x1 = x * self.cell_size + self.cell_size // 4
                y1 = y * self.cell_size + self.cell_size // 4
                x2 = x1 + self.cell_size // 2
                y2 = y1 + self.cell_size // 2
                
                progress = i / len(self.path)
                hue = (progress + self.time * 0.2) % 1.0
                color = self.hsv_to_rgb(hue, 0.9, 1.0)
                
                self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color)
        
        # 绘制入口和出口
        # 入口
        entrance_color = self.hsv_to_rgb(0.3, 0.9, 1.0)
        self.canvas.create_rectangle(
            0, self.cell_size, 
            self.cell_size, self.cell_size * 2,
            fill=entrance_color, outline=entrance_color
        )
        
        # 出口
        exit_color = self.hsv_to_rgb(0.7, 0.9, 1.0)
        self.canvas.create_rectangle(
            (self.cols-1) * self.cell_size, (self.rows-2) * self.cell_size,
            self.cols * self.cell_size, (self.rows-1) * self.cell_size,
            fill=exit_color, outline=exit_color
        )

class SpectrumPyramidEffect(VisualEffect):
    """频谱金字塔"""
    def draw(self):
        num_levels = 8
        
        for level in range(num_levels):
            size = 200 - level * 20
            y_offset = level * 15
            
            # 计算四个角的坐标
            top_left = (self.center_x - size, self.center_y - size + y_offset)
            top_right = (self.center_x + size, self.center_y - size + y_offset)
            bottom_left = (self.center_x - size, self.center_y + size + y_offset)
            bottom_right = (self.center_x + size, self.center_y + size + y_offset)
            
            # 获取对应频带的能量
            band_idx = int((level / num_levels) * 64)
            energy = self.audio.get_band_energy(band_idx)
            
            # 金字塔变形
            deformation = math.sin(self.time + level * 0.5) * energy * 20
            
            # 绘制金字塔的四个面
            
            # 前面
            points_front = [
                self.center_x, self.center_y - size + y_offset + deformation,
                self.center_x - size, self.center_y + y_offset,
                self.center_x + size, self.center_y + y_offset
            ]
            
            hue_front = (level / num_levels + self.time * 0.1) % 1.0
            color_front = self.hsv_to_rgb(hue_front, 0.8, 0.7)
            
            self.canvas.create_polygon(points_front, fill=color_front, outline=color_front, width=1)
            
            # 左侧面
            points_left = [
                self.center_x, self.center_y - size + y_offset + deformation,
                self.center_x - size, self.center_y + y_offset,
                self.center_x, self.center_y + size + y_offset
            ]
            
            hue_left = (level / num_levels + self.time * 0.1 + 0.2) % 1.0
            color_left = self.hsv_to_rgb(hue_left, 0.8, 0.6)
            
            self.canvas.create_polygon(points_left, fill=color_left, outline=color_left, width=1)
            
            # 右侧面
            points_right = [
                self.center_x, self.center_y - size + y_offset + deformation,
                self.center_x + size, self.center_y + y_offset,
                self.center_x, self.center_y + size + y_offset
            ]
            
            hue_right = (level / num_levels + self.time * 0.1 + 0.4) % 1.0
            color_right = self.hsv_to_rgb(hue_right, 0.8, 0.6)
            
            self.canvas.create_polygon(points_right, fill=color_right, outline=color_right, width=1)
        
        # 绘制金字塔顶
        top_color = self.hsv_to_rgb(self.time * 0.2, 0.9, 1.0)
        self.canvas.create_oval(
            self.center_x - 10, self.center_y - 160,
            self.center_x + 10, self.center_y - 140,
            fill=top_color, outline=top_color
        )

# ==================== 主程序 ====================
class UltimateWMPVisualizer:
    """终极版WMP可视化程序"""
    
    def __init__(self, width=800, height=600):
        # 主窗口
        self.root = tk.Tk()
        self.root.title("Windows Media Player Visualizer - 终极版")
        self.root.configure(bg='black')
        
        # 主框架
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧画布区域
        canvas_frame = tk.Frame(main_frame, bg='black')
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 画布
        self.canvas = tk.Canvas(canvas_frame, width=width, height=height, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧效果列表区域
        list_frame = tk.Frame(main_frame, bg='#222222', width=200)
        list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        list_frame.pack_propagate(False)  # 固定宽度
        
        # 效果列表标题
        tk.Label(list_frame, text="可视化效果列表", 
                font=("Arial", 12, "bold"),
                fg='white', bg='#222222').pack(pady=(10, 5))
        
        # 创建滚动条
        list_container = tk.Frame(list_frame, bg='#111111')
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 效果列表容器（使用Canvas实现滚动）
        self.list_canvas = tk.Canvas(list_container, bg='#111111', 
                                   yscrollcommand=scrollbar.set,
                                   highlightthickness=0)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.list_canvas.yview)
        
        # 内部框架用于包含效果项
        self.effects_inner_frame = tk.Frame(self.list_canvas, bg='#111111')
        self.list_canvas.create_window((0, 0), window=self.effects_inner_frame, anchor='nw')
        
        # 底部控制面板
        control_frame = tk.Frame(self.root, bg='#333333')
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # 自动切换按钮
        self.auto_switch = True
        self.auto_switch_btn = tk.Button(
            control_frame, 
            text="自动切换: 开启",
            command=self.toggle_auto_switch,
            bg='#666666', fg='white',
            font=("Arial", 10),
            relief='flat', padx=20, pady=5
        )
        self.auto_switch_btn.pack(pady=5)
        
        # 参数
        self.width = width
        self.height = height
        
        # 鼠标位置
        self.mouse_pos = [None, None]
        self.mouse_effect_enabled = True  # 鼠标互动总开关
        
        # 音频模拟
        self.audio = AudioSimulator()
        
        # 效果注册 - 为每个效果分配编号
        self.effects = {
            "01. 条形图": BarsEffect,
            "02. 尖峰": SpikesEffect,
            "03. 波形": WaveformEffect,
            "04. 漩涡": VortexEffect,
            "05. 频谱环": SpectrumCircleEffect,
            "06. 矩阵雨": MatrixRainEffect,
            "07. 等离子": PlasmaEffect,
            "08. 瀑布图": WaterfallEffect,
            "09. 火焰": FireEffect,
            "10. 分形": FractalEffect,
            "11. 几何图案": GeometricEffect,
            "12. 声纳": SonarEffect,
            "13. 频谱射线": SpectrumRaysEffect,
            "14. 跳动的心": HeartEffect,
            "15. 星域": StarfieldEffect,
            "16. 万花筒": KaleidoscopeEffect,
            "17. 频谱波浪": SpectrumWaveEffect,
            "18. 3D立方体": Cube3DEffect,
            "19. 3D频谱波浪": SpectrumWaves3DEffect,
            "20. 音频莫尔条纹": AudioMoireEffect,
            "21. 频谱球体": SpectrumOrbEffect,
            "22. 音频花朵": AudioFlowerEffect,
            "23. 频谱螺旋": SpectrumSpiralEffect,
            "24. 音频网格": AudioGridEffect,
            "25. 频谱涟漪": SpectrumRipplesEffect,
            "26. 音频迷宫": AudioMazeEffect,
            "27. 频谱金字塔": SpectrumPyramidEffect,
            "28. 元胞自动机": CellularAutomatonEffect,
            "29. 环形脉冲": RingPulseEffect,
            "30. 极坐标网格": PolarGridEffect,
            "31. 粒子爆发": ParticleBurstEffect,
            "32. 音频指纹": AudioFingerprintEffect,
            "33. 频谱山峦": SpectrumMountainEffect,
            "34. 环形频谱": CircularSpectrumEffect,
            "35. DNA螺旋": DNAHelixEffect,
            "36. 音符雨": NoteRainEffect,
            "37. 声音漩涡": SoundVortexEffect,
            "38. 霓虹隧道": NeonTunnelEffect,
            "39. 水波涟漪": RippleEffect,
            "40. 3D旋转环": MobiusStripEffect,
            "41. 分形树": FractalTreeEffect,
            "42. 超立方体": HyperCubeEffect,
            "43. 频谱渐变墙": GradientWallEffect,
            "44. 极光效果": AuroraEffect,
            "45. 星光闪烁": StarTwinkleEffect,
            "46. 音频弹跳球": BouncingBallsEffect,
            "47. 粒子连线": ParticleConnectEffect,
            "48. 鼠标跟随": MouseFollowerEffect
        }
        
        # 自动切换 - 随机区间(10-20秒)
        self.switch_interval_min = 10
        self.switch_interval_max = 20
        
        # 创建效果列表
        self.create_effects_list()
        
        # 当前效果
        self.current_effect_name = "01. 条形图"
        self.current_effect = self.create_effect_instance(self.current_effect_name)
        
        self.switch_interval = random.randint(self.switch_interval_min, self.switch_interval_max)
        self.last_switch_time = time.time()
        
        # 性能监控
        self.perf = PerformanceMonitor()
        self.last_frame_time = time.time()
        
        # 高亮当前效果
        self.highlight_current_effect()
        
        # 更新滚动区域
        self.effects_inner_frame.update_idletasks()
        self.list_canvas.config(scrollregion=self.list_canvas.bbox("all"))
        
        # 绑定鼠标事件
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<Button-3>", self.on_mouse_click_right)
        
        # 启动主循环
        self.running = True
        self.update_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_effect_instance(self, effect_name):
        """创建效果实例，支持传递鼠标位置"""
        effect_class = self.effects.get(effect_name)
        if effect_class:
            # 如果是鼠标跟随效果，传递鼠标位置引用
            if effect_name == "48. 鼠标跟随":
                return effect_class(self.canvas, self.width, self.height, self.audio, self.mouse_pos)
            return effect_class(self.canvas, self.width, self.height, self.audio)
        return None
    
    def on_mouse_move(self, event):
        """鼠标移动事件"""
        self.mouse_pos[0] = event.x
        self.mouse_pos[1] = event.y
    
    def on_mouse_click(self, event):
        """鼠标左键点击事件"""
        # 在鼠标位置添加涟漪效果
        if self.current_effect is not None:
            add_ripple = getattr(self.current_effect, 'add_ripple', None)
            if add_ripple is not None:
                add_ripple(event.x, event.y)
    
    def on_mouse_click_right(self, event):
        """鼠标右键点击事件 - 切换鼠标互动开关"""
        self.mouse_effect_enabled = not self.mouse_effect_enabled
        # 隐藏/显示鼠标指示器效果
        if not self.mouse_effect_enabled:
            self.mouse_pos = [None, None]
        
    def create_effects_list(self):
        """创建效果列表"""
        self.effect_labels = {}
        
        for effect_name in self.effects.keys():
            # 创建效果项
            effect_frame = tk.Frame(self.effects_inner_frame, bg='#111111')
            effect_frame.pack(fill=tk.X, pady=2)
            
            # 效果名称标签
            label = tk.Label(
                effect_frame, 
                text=f"• {effect_name}",
                font=("Arial", 10),
                fg='#888888',
                bg='#111111',
                anchor='w',
                padx=10,
                pady=5
            )
            label.pack(fill=tk.X)
            
            # 保存引用
            self.effect_labels[effect_name] = (label, effect_frame)
        
        # 添加说明文本
        tk.Label(
            self.effects_inner_frame,
            text=f"\n效果列表为只读视图\n自动切换({self.switch_interval_min}-{self.switch_interval_max}秒)\n总共{len(self.effects)}种可视化效果\n\n鼠标互动:\n• 移动鼠标跟随效果\n• 左键点击添加涟漪\n• 右键开关鼠标互动",
            font=("Arial", 8),
            fg='#666666',
            bg='#111111',
            wraplength=180,
            justify='left'
        ).pack(pady=(20, 5))
    
    def highlight_current_effect(self):
        """高亮显示当前效果"""
        for effect_name, (label, frame) in self.effect_labels.items():
            if effect_name == self.current_effect_name:
                label.config(fg='#00FF00', font=("Arial", 10, "bold"))
                frame.config(bg='#333333')
            else:
                label.config(fg='#888888', font=("Arial", 10))
                frame.config(bg='#111111')
    
    def set_effect(self, effect_name):
        """设置当前效果"""
        if effect_name in self.effects:
            self.current_effect_name = effect_name
            self.current_effect = self.create_effect_instance(effect_name)
            self.highlight_current_effect()
    
    def toggle_auto_switch(self):
        """切换自动切换"""
        self.auto_switch = not self.auto_switch
        if self.auto_switch:
            self.auto_switch_btn.config(text="自动切换: 开启")
        else:
            self.auto_switch_btn.config(text="自动切换: 关闭")
        
    def update_frame(self):
        """更新帧"""
        if not self.running:
            return
        
        self.perf.start_frame()
        
        # 更新音频数据
        self.audio.update()
        
        # 自动切换效果
        if self.auto_switch and time.time() - self.last_switch_time > self.switch_interval:
            effect_names = list(self.effects.keys())
            current_idx = effect_names.index(self.current_effect_name)
            next_idx = (current_idx + 1) % len(effect_names)
            self.set_effect(effect_names[next_idx])
            self.last_switch_time = time.time()
            # 重新生成随机切换间隔
            self.switch_interval = random.randint(self.switch_interval_min, self.switch_interval_max)
        
        # 清空画布
        self.canvas.delete("all")
        
        # 计算时间增量
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        # 更新并绘制效果
        try:
            if self.current_effect is not None:
                self.current_effect.update(dt)
                self.current_effect.draw()
        except Exception as e:
            # 如果效果绘制出错，显示错误信息
            error_text = f"效果 '{self.current_effect_name}' 绘制出错:\n{str(e)}"
            self.canvas.create_text(
                self.width // 2, self.height // 2,
                text=error_text,
                fill='red',
                font=("Arial", 12),
                justify='center'
            )
        
        # 绘制性能信息
        fps = self.perf.get_fps()
        avg_frame_time = self.perf.get_avg_frame_time()
        
        # 信息显示
        effect_number = self.current_effect_name.split(".")[0] if "." in self.current_effect_name else "??"
        effect_name_only = self.current_effect_name.split(". ", 1)[1] if ". " in self.current_effect_name else self.current_effect_name
        
        info_text = f"效果 {effect_number}: {effect_name_only}\n"
        info_text += f"帧率: {fps:.1f} FPS\n"
        info_text += f"帧时间: {avg_frame_time*1000:.1f}ms\n"
        
        if self.auto_switch:
            remaining = self.switch_interval - (time.time() - self.last_switch_time)
            if remaining > 0:
                info_text += f"切换倒计时: {remaining:.0f}秒"
        
        # 在画布上绘制信息
        self.canvas.create_text(
            10, 10, 
            text=info_text,
            anchor='nw',
            fill='white',
            font=("Arial", 10)
        )
        
        # 在画布上绘制标题
        self.canvas.create_text(
            self.width // 2, 20,
            text=f"Windows Media Player 可视化效果 - 效果{effect_number}: {effect_name_only}",
            fill='#00FF00',
            font=("Arial", 16, "bold")
        )
        
        # 绘制效果总数
        self.canvas.create_text(
            self.width - 10, self.height - 10,
            text=f"总效果数: {len(self.effects)}",
            anchor='se',
            fill='#888888',
            font=("Arial", 9)
        )
        
        # 绘制效果编号
        effect_names = list(self.effects.keys())
        current_idx = effect_names.index(self.current_effect_name)
        self.canvas.create_text(
            self.width - 10, 10,
            text=f"当前效果: {current_idx + 1}/{len(self.effects)}",
            anchor='ne',
            fill='#888888',
            font=("Arial", 9)
        )
        
        # 结束帧
        self.perf.end_frame()
        
        # 下一帧
        self.root.after(16, self.update_frame)  # 约60fps
    
    def on_closing(self):
        """窗口关闭事件"""
        self.running = False
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        # 设置窗口大小
        self.root.geometry("1000x700")
        
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()

# ==================== 启动程序 ====================
if __name__ == "__main__":
    # 创建并运行可视化程序
    app = UltimateWMPVisualizer(width=800, height=600)
    app.run()