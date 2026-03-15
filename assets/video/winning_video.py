#!/usr/bin/env python3
"""
FlowState-QMD Hackathon Video - NEURAL MATRIX EDITION

Design: Cyberpunk neural network aesthetic with:
- Matrix-style data rain
- Glowing neural nodes and connections
- Pulsing energy effects
- Neon color palette
- Dynamic particle systems
- Clean, spacious layouts

Target: 90 seconds, 1080p, 30fps
"""

import math
import os
import random
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# === CONFIG ===
WIDTH, HEIGHT = 1920, 1080
FPS = 30
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT = SCRIPT_DIR / "flowstate_winning.mp4"
FRAMES_DIR = SCRIPT_DIR / "winning_frames"

# Generous safe area
MARGIN = 140
SAFE_LEFT = MARGIN
SAFE_RIGHT = WIDTH - MARGIN
SAFE_TOP = 100
SAFE_BOTTOM = HEIGHT - 80
SAFE_WIDTH = SAFE_RIGHT - SAFE_LEFT
SAFE_HEIGHT = SAFE_BOTTOM - SAFE_TOP
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2

# === NEURAL MATRIX COLOR PALETTE ===
COLORS = {
    # Backgrounds
    "void": (2, 4, 12),
    "deep": (4, 8, 20),
    
    # Neon accents
    "cyan": (0, 255, 220),
    "pink": (255, 50, 180),
    "purple": (180, 80, 255),
    "green": (50, 255, 150),
    "orange": (255, 150, 50),
    "red": (255, 70, 90),
    "blue": (80, 150, 255),
    
    # Text
    "white": (255, 255, 255),
    "ghost": (160, 180, 200),
    "dim": (80, 100, 120),
    
    # Effects
    "glow_cyan": (0, 180, 160),
    "glow_pink": (180, 40, 130),
}

# Seed for reproducible "random" effects
random.seed(42)

# === FONTS ===
def load_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    paths = {
        "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"],
        "regular": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"],
        "mono": ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf"],
    }
    for path in paths.get(weight, paths["regular"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

FONT_HERO = load_font(90, "bold")
FONT_TITLE = load_font(56, "bold")
FONT_SUBTITLE = load_font(36, "bold")
FONT_BODY = load_font(30, "regular")
FONT_SMALL = load_font(24, "regular")
FONT_MONO = load_font(22, "mono")
FONT_TINY = load_font(16, "mono")
FONT_HUGE = load_font(140, "bold")

# === EASING FUNCTIONS ===
def ease_out(t): return 1 - (1 - t) ** 3
def ease_in_out(t): return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
def ease_elastic(t): 
    if t == 0 or t == 1: return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * 2.094) + 1
def lerp(a, b, t): return a + (b - a) * t
def lerp_color(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

# === MATRIX EFFECTS ===

class MatrixRain:
    """Matrix-style falling code effect."""
    def __init__(self, columns=60):
        self.columns = columns
        self.drops = []
        self.chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        for i in range(columns):
            x = int(i * (WIDTH / columns))
            y = random.randint(-HEIGHT, 0)
            speed = random.uniform(3, 8)
            length = random.randint(8, 20)
            self.drops.append({"x": x, "y": y, "speed": speed, "length": length, "chars": []})
            for j in range(length):
                self.drops[-1]["chars"].append(random.choice(self.chars))
    
    def draw(self, draw: ImageDraw.ImageDraw, progress: float, intensity: float = 0.3):
        for drop in self.drops:
            y = (drop["y"] + progress * 1000 * drop["speed"]) % (HEIGHT + 500) - 200
            for j, char in enumerate(drop["chars"]):
                cy = y + j * 20
                if 0 <= cy <= HEIGHT:
                    # Head is brightest
                    if j == 0:
                        color = COLORS["cyan"]
                    elif j < 3:
                        alpha = 1 - j * 0.2
                        color = lerp_color(COLORS["cyan"], COLORS["green"], 0.5)
                        color = lerp_color(COLORS["void"], color, alpha * intensity)
                    else:
                        alpha = max(0, 1 - j / drop["length"])
                        color = lerp_color(COLORS["void"], COLORS["green"], alpha * intensity * 0.5)
                    
                    if color[0] + color[1] + color[2] > 30:  # Only draw visible chars
                        draw.text((drop["x"], cy), char, font=FONT_TINY, fill=color)

# Global matrix rain instance
MATRIX = MatrixRain(50)

class NeuralNetwork:
    """Animated neural network visualization."""
    def __init__(self):
        self.nodes = []
        self.connections = []
        # Create node positions in layers
        layers = [4, 6, 8, 6, 4]
        x_step = WIDTH // (len(layers) + 1)
        for layer_idx, count in enumerate(layers):
            x = x_step * (layer_idx + 1)
            y_step = HEIGHT // (count + 1)
            for i in range(count):
                y = y_step * (i + 1)
                self.nodes.append({"x": x, "y": y, "layer": layer_idx})
        
        # Create connections between adjacent layers
        node_idx = 0
        for layer_idx, count in enumerate(layers[:-1]):
            next_count = layers[layer_idx + 1]
            next_start = node_idx + count
            for i in range(count):
                for j in range(next_count):
                    if random.random() < 0.6:  # Not all connections
                        self.connections.append((node_idx + i, next_start + j))
            node_idx += count
    
    def draw(self, draw: ImageDraw.ImageDraw, progress: float, intensity: float = 0.3):
        # Draw connections with flowing energy
        for idx, (n1, n2) in enumerate(self.connections):
            node1, node2 = self.nodes[n1], self.nodes[n2]
            
            # Pulse effect
            pulse = (math.sin(progress * 10 + idx * 0.5) + 1) / 2
            alpha = 0.1 + pulse * 0.2 * intensity
            color = lerp_color(COLORS["void"], COLORS["purple"], alpha)
            
            draw.line([(node1["x"], node1["y"]), (node2["x"], node2["y"])], fill=color, width=1)
            
            # Energy packet traveling along connection
            if random.random() < 0.3:
                t = (progress * 3 + idx * 0.1) % 1
                px = lerp(node1["x"], node2["x"], t)
                py = lerp(node1["y"], node2["y"], t)
                glow_color = lerp_color(COLORS["void"], COLORS["cyan"], intensity * 0.8)
                draw.ellipse([px-3, py-3, px+3, py+3], fill=glow_color)
        
        # Draw nodes with glow
        for idx, node in enumerate(self.nodes):
            pulse = (math.sin(progress * 8 + idx * 0.7) + 1) / 2
            size = 4 + pulse * 2
            
            # Outer glow
            glow_size = size + 6
            glow_color = lerp_color(COLORS["void"], COLORS["cyan"], 0.2 * intensity)
            draw.ellipse([node["x"]-glow_size, node["y"]-glow_size, 
                         node["x"]+glow_size, node["y"]+glow_size], fill=glow_color)
            
            # Core
            core_color = lerp_color(COLORS["cyan"], COLORS["white"], pulse * 0.3)
            core_color = lerp_color(COLORS["void"], core_color, intensity)
            draw.ellipse([node["x"]-size, node["y"]-size, 
                         node["x"]+size, node["y"]+size], fill=core_color)

NEURAL_NET = NeuralNetwork()

def draw_hex_grid(draw: ImageDraw.ImageDraw, progress: float, intensity: float = 0.15):
    """Draw a subtle hexagonal grid pattern."""
    hex_size = 40
    for row in range(int(HEIGHT / hex_size) + 2):
        for col in range(int(WIDTH / hex_size) + 2):
            x = col * hex_size * 1.5
            y = row * hex_size * 1.732 + (col % 2) * hex_size * 0.866
            
            # Pulse based on position
            pulse = (math.sin(progress * 4 + x * 0.01 + y * 0.01) + 1) / 2
            alpha = pulse * intensity
            color = lerp_color(COLORS["void"], COLORS["cyan"], alpha)
            
            # Draw hexagon outline
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                px = x + hex_size * 0.4 * math.cos(angle)
                py = y + hex_size * 0.4 * math.sin(angle)
                points.append((px, py))
            
            if all(0 <= p[0] <= WIDTH and 0 <= p[1] <= HEIGHT for p in points):
                draw.polygon(points, outline=color)

def draw_energy_burst(draw: ImageDraw.ImageDraw, cx: int, cy: int, progress: float, color: tuple):
    """Draw an expanding energy burst effect."""
    max_radius = 300
    num_rings = 5
    
    for i in range(num_rings):
        ring_progress = (progress + i * 0.15) % 1
        radius = ring_progress * max_radius
        alpha = (1 - ring_progress) * 0.6
        
        if alpha > 0.05:
            ring_color = lerp_color(COLORS["void"], color, alpha)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=ring_color, width=2)

def draw_scan_lines(draw: ImageDraw.ImageDraw, intensity: float = 0.1):
    """Draw CRT-style scan lines."""
    for y in range(0, HEIGHT, 3):
        alpha = intensity * 0.5
        color = lerp_color(COLORS["void"], (0, 0, 0), alpha)
        draw.line([(0, y), (WIDTH, y)], fill=color, width=1)

def draw_glowing_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font, color: tuple, glow_color: tuple = None):
    """Draw text with a neon glow effect."""
    glow_color = glow_color or color
    
    # Draw glow layers (simulated blur)
    for offset in [4, 3, 2]:
        glow = lerp_color(COLORS["void"], glow_color, 0.15)
        draw.text((x - offset, y), text, font=font, fill=glow)
        draw.text((x + offset, y), text, font=font, fill=glow)
        draw.text((x, y - offset), text, font=font, fill=glow)
        draw.text((x, y + offset), text, font=font, fill=glow)
    
    # Main text
    draw.text((x, y), text, font=font, fill=color)

def draw_neon_box(draw: ImageDraw.ImageDraw, box: tuple, color: tuple, fill: tuple = None):
    """Draw a box with neon glow border."""
    x1, y1, x2, y2 = box
    fill = fill or lerp_color(COLORS["void"], color, 0.08)
    
    # Glow
    for i in range(3, 0, -1):
        glow = lerp_color(COLORS["void"], color, 0.1 * (4 - i))
        draw.rounded_rectangle([x1-i, y1-i, x2+i, y2+i], radius=12, outline=glow, width=2)
    
    # Fill and border
    draw.rounded_rectangle(box, radius=10, fill=fill, outline=color, width=2)

def get_text_size(text: str, font) -> tuple:
    """Get text dimensions."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font, color: tuple, glow: bool = True):
    """Draw centered text with optional glow."""
    w, h = get_text_size(text, font)
    x = (WIDTH - w) // 2
    if glow:
        draw_glowing_text(draw, text, x, y, font, color)
    else:
        draw.text((x, y), text, font=font, fill=color)


# === SCENE GENERATORS ===

def scene_intro(progress: float) -> Image.Image:
    """Epic intro with matrix rain and neural network."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Background effects - fade in
    bg_intensity = ease_out(min(progress * 2, 1.0))
    MATRIX.draw(draw, progress, intensity=bg_intensity * 0.25)
    NEURAL_NET.draw(draw, progress, intensity=bg_intensity * 0.15)
    
    # Central burst
    if progress > 0.3:
        burst_prog = (progress - 0.3) / 0.7
        draw_energy_burst(draw, CENTER_X, CENTER_Y, burst_prog, COLORS["cyan"])
    
    # Main text reveal
    if progress > 0.15:
        alpha = ease_out(min((progress - 0.15) * 2.5, 1.0))
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "What if your AI agent", 340, FONT_TITLE, color)
    
    if progress > 0.4:
        alpha = ease_elastic(min((progress - 0.4) * 2, 1.0))
        color = lerp_color(COLORS["void"], COLORS["cyan"], alpha)
        draw_centered(draw, "already knew", 440, FONT_HERO, color)
    
    if progress > 0.6:
        alpha = ease_out(min((progress - 0.6) * 2.5, 1.0))
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "before it searched?", 560, FONT_TITLE, color)
    
    # Scan line effect
    draw_scan_lines(draw, 0.05)
    
    return img


def scene_problem(progress: float) -> Image.Image:
    """The problem visualization - stutter loop."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Subtle background
    draw_hex_grid(draw, progress, 0.08)
    MATRIX.draw(draw, progress, intensity=0.1)
    
    # Title
    draw_glowing_text(draw, "THE STUTTER LOOP", SAFE_LEFT, SAFE_TOP, FONT_SUBTITLE, COLORS["red"])
    draw.text((SAFE_LEFT, SAFE_TOP + 50), "What happens every time an agent needs context", font=FONT_BODY, fill=COLORS["ghost"])
    
    # Circular flow diagram - FUN spinning visualization
    center_x, center_y = CENTER_X - 150, CENTER_Y + 50
    radius = 200
    
    steps = [
        ("🗣️ User asks", COLORS["white"]),
        ("🤔 Agent thinks", COLORS["orange"]),
        ("🔍 Search needed!", COLORS["red"]),
        ("⏳ Fetching...", COLORS["red"]),
        ("📄 Processing", COLORS["orange"]),
        ("✓ Finally answer", COLORS["ghost"]),
    ]
    
    # Draw circular connections
    for i in range(len(steps)):
        angle1 = (i / len(steps)) * 2 * math.pi - math.pi / 2
        angle2 = ((i + 1) / len(steps)) * 2 * math.pi - math.pi / 2
        
        x1 = center_x + radius * math.cos(angle1)
        y1 = center_y + radius * math.sin(angle1)
        x2 = center_x + radius * math.cos(angle2)
        y2 = center_y + radius * math.sin(angle2)
        
        # Animated arc
        visible = progress * len(steps) > i
        if visible:
            color = lerp_color(COLORS["void"], COLORS["red"], 0.4)
            # Draw arc as line segments
            for t in range(20):
                t1 = t / 20
                t2 = (t + 1) / 20
                a1 = angle1 + (angle2 - angle1) * t1
                a2 = angle1 + (angle2 - angle1) * t2
                px1 = center_x + radius * math.cos(a1)
                py1 = center_y + radius * math.sin(a1)
                px2 = center_x + radius * math.cos(a2)
                py2 = center_y + radius * math.sin(a2)
                draw.line([(px1, py1), (px2, py2)], fill=color, width=3)
    
    # Draw step nodes
    for i, (label, color) in enumerate(steps):
        step_progress = max(0, min((progress - i * 0.12) * 4, 1.0))
        if step_progress <= 0:
            continue
        
        angle = (i / len(steps)) * 2 * math.pi - math.pi / 2
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Node with glow
        alpha = ease_out(step_progress)
        node_color = lerp_color(COLORS["void"], color, alpha)
        
        # Glow
        for r in range(25, 10, -5):
            glow = lerp_color(COLORS["void"], color, alpha * 0.1)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=glow)
        
        # Core
        draw.ellipse([x-15, y-15, x+15, y+15], fill=node_color, outline=COLORS["white"], width=2)
        
        # Label
        text_x = x + 30 if angle > -math.pi/2 and angle < math.pi/2 else x - 180
        text_y = y - 12
        draw.text((text_x, text_y), label, font=FONT_BODY, fill=lerp_color(COLORS["void"], color, alpha))
    
    # Timer callout on right
    if progress > 0.7:
        alpha = ease_out((progress - 0.7) * 3)
        box_x = WIDTH - MARGIN - 380
        draw_neon_box(draw, (box_x, 280, box_x + 360, 520), COLORS["red"])
        
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw.text((box_x + 30, 310), "Per-question cost:", font=FONT_BODY, fill=color)
        
        color = lerp_color(COLORS["void"], COLORS["red"], alpha)
        draw_glowing_text(draw, "2-4s", box_x + 60, 370, FONT_HUGE, color)
        
        color = lerp_color(COLORS["void"], COLORS["ghost"], alpha)
        draw.text((box_x + 30, 480), "Flow state: BROKEN", font=FONT_SMALL, fill=color)
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_transition(progress: float) -> Image.Image:
    """Dramatic transition - "But what if..." """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Energy building
    if progress < 0.5:
        # Building tension
        intensity = progress * 2
        NEURAL_NET.draw(draw, progress * 3, intensity=intensity * 0.4)
        
        alpha = ease_out(progress * 2)
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "But what if...", CENTER_Y - 50, FONT_HERO, color)
    else:
        # EXPLOSION of color
        burst_prog = (progress - 0.5) * 2
        
        # Multiple bursts
        draw_energy_burst(draw, CENTER_X, CENTER_Y, burst_prog, COLORS["cyan"])
        draw_energy_burst(draw, CENTER_X - 200, CENTER_Y, burst_prog * 0.8, COLORS["pink"])
        draw_energy_burst(draw, CENTER_X + 200, CENTER_Y, burst_prog * 0.8, COLORS["purple"])
        
        MATRIX.draw(draw, progress, intensity=0.4)
        
        if progress > 0.7:
            alpha = ease_elastic((progress - 0.7) * 3)
            draw_centered(draw, "FlowState-QMD", CENTER_Y - 80, FONT_HERO, 
                         lerp_color(COLORS["void"], COLORS["cyan"], alpha))
            
            alpha2 = ease_out((progress - 0.8) * 5) if progress > 0.8 else 0
            draw_centered(draw, "Anticipatory Memory for AI Agents", CENTER_Y + 60, FONT_SUBTITLE,
                         lerp_color(COLORS["void"], COLORS["white"], alpha2))
    
    draw_scan_lines(draw, 0.04)
    return img


def scene_solution(progress: float) -> Image.Image:
    """The solution explained - cleaner design."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Subtle background
    draw_hex_grid(draw, progress, 0.05)
    NEURAL_NET.draw(draw, progress, intensity=0.08)
    
    # Title
    draw_glowing_text(draw, "HOW IT WORKS", SAFE_LEFT, SAFE_TOP, FONT_SUBTITLE, COLORS["cyan"])
    
    # Three simple steps - CLEAN LAYOUT, NO OVERLAP
    steps = [
        {"icon": "👁️", "title": "WATCH", "desc": "Monitor session in real-time", "color": COLORS["purple"]},
        {"icon": "🧠", "title": "ANTICIPATE", "desc": "Pre-fetch relevant memories", "color": COLORS["cyan"]},
        {"icon": "⚡", "title": "INJECT", "desc": "Context ready at turn start", "color": COLORS["green"]},
    ]
    
    # Calculate positions - evenly spaced
    card_width = 450
    total_width = card_width * 3 + 80 * 2  # 3 cards + 2 gaps
    start_x = (WIDTH - total_width) // 2
    card_y = 220
    card_height = 320
    
    for i, step in enumerate(steps):
        step_progress = max(0, min((progress - i * 0.2) * 2, 1.0))
        if step_progress <= 0:
            continue
        
        x = start_x + i * (card_width + 80)
        alpha = ease_out(step_progress)
        
        # Card with glow
        card_color = lerp_color(COLORS["void"], step["color"], alpha * 0.15)
        border_color = lerp_color(COLORS["void"], step["color"], alpha)
        
        # Glow effect
        for g in range(3):
            glow = lerp_color(COLORS["void"], step["color"], alpha * 0.08 * (3-g))
            draw.rounded_rectangle([x-g*2, card_y-g*2, x+card_width+g*2, card_y+card_height+g*2], 
                                   radius=16, outline=glow, width=2)
        
        draw.rounded_rectangle([x, card_y, x+card_width, card_y+card_height], 
                               radius=14, fill=card_color, outline=border_color, width=2)
        
        # Icon - big and centered
        icon_w, _ = get_text_size(step["icon"], FONT_HERO)
        draw.text((x + (card_width - icon_w) // 2, card_y + 30), step["icon"], font=FONT_HERO, 
                 fill=lerp_color(COLORS["void"], step["color"], alpha))
        
        # Title
        title_w, _ = get_text_size(step["title"], FONT_SUBTITLE)
        draw.text((x + (card_width - title_w) // 2, card_y + 150), step["title"], font=FONT_SUBTITLE,
                 fill=lerp_color(COLORS["void"], COLORS["white"], alpha))
        
        # Description
        desc_w, _ = get_text_size(step["desc"], FONT_SMALL)
        draw.text((x + (card_width - desc_w) // 2, card_y + 210), step["desc"], font=FONT_SMALL,
                 fill=lerp_color(COLORS["void"], COLORS["ghost"], alpha))
        
        # Animated energy line connecting to next
        if i < 2 and step_progress > 0.5:
            line_prog = (step_progress - 0.5) * 2
            arrow_x = x + card_width + 10
            arrow_end = arrow_x + 60 * line_prog
            arrow_y = card_y + card_height // 2
            
            arrow_color = lerp_color(COLORS["void"], COLORS["cyan"], alpha * 0.8)
            draw.line([(arrow_x, arrow_y), (arrow_end, arrow_y)], fill=arrow_color, width=3)
            
            # Arrow head
            if line_prog > 0.8:
                draw.polygon([(arrow_end, arrow_y - 8), (arrow_end + 12, arrow_y), (arrow_end, arrow_y + 8)], 
                            fill=arrow_color)
    
    # Bottom result bar
    if progress > 0.85:
        alpha = ease_out((progress - 0.85) * 6)
        
        result_y = 620
        draw_neon_box(draw, (SAFE_LEFT, result_y, SAFE_RIGHT, result_y + 120), COLORS["cyan"])
        
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "Context loads in 48ms — before the agent even starts thinking", result_y + 40, FONT_BODY, color, glow=False)
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_metrics(progress: float) -> Image.Image:
    """Animated metrics with fun counting effect."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Background
    MATRIX.draw(draw, progress, intensity=0.08)
    draw_hex_grid(draw, progress, 0.04)
    
    # Title
    draw_glowing_text(draw, "MEASURED RESULTS", SAFE_LEFT, SAFE_TOP, FONT_SUBTITLE, COLORS["green"])
    draw.text((SAFE_LEFT, SAFE_TOP + 50), "Apple M4, 24GB • 5,000 documents", font=FONT_BODY, fill=COLORS["ghost"])
    
    # Metrics in a 2x2 grid - properly positioned
    metrics = [
        {"value": 50, "suffix": "x", "label": "Faster Response", "color": COLORS["cyan"]},
        {"value": 89, "suffix": "%", "label": "Fewer Tool Calls", "color": COLORS["green"]},
        {"value": 73, "suffix": "%", "label": "Cache Hit Rate", "color": COLORS["purple"]},
        {"value": 48, "suffix": "ms", "label": "Average Latency", "color": COLORS["orange"]},
    ]
    
    card_w, card_h = 650, 200
    gap_x, gap_y = 60, 50
    grid_w = card_w * 2 + gap_x
    grid_h = card_h * 2 + gap_y
    start_x = (WIDTH - grid_w) // 2
    start_y = 200
    
    for i, m in enumerate(metrics):
        row, col = i // 2, i % 2
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        
        delay = i * 0.15
        mp = max(0, min((progress - delay) * 2.5, 1.0))
        if mp <= 0:
            continue
        
        alpha = ease_out(mp)
        
        # Card
        draw_neon_box(draw, (x, y, x + card_w, y + card_h), m["color"])
        
        # Animated value - counting up effect!
        if mp < 0.8:
            displayed = int(m["value"] * (mp / 0.8))
        else:
            displayed = m["value"]
        
        value_text = f"{displayed}{m['suffix']}"
        value_color = lerp_color(COLORS["void"], m["color"], alpha)
        draw_glowing_text(draw, value_text, x + 40, y + 35, FONT_HUGE, value_color)
        
        # Label
        draw.text((x + 40, y + 150), m["label"], font=FONT_BODY, 
                 fill=lerp_color(COLORS["void"], COLORS["ghost"], alpha))
        
        # Fun particle burst when counter finishes
        if 0.75 < mp < 0.95:
            burst_prog = (mp - 0.75) / 0.2
            cx, cy = x + 200, y + 100
            for j in range(8):
                angle = j * math.pi / 4
                dist = burst_prog * 60
                px = cx + dist * math.cos(angle)
                py = cy + dist * math.sin(angle)
                size = (1 - burst_prog) * 6
                draw.ellipse([px-size, py-size, px+size, py+size], fill=m["color"])
    
    # Bottom comparison
    if progress > 0.85:
        alpha = ease_out((progress - 0.85) * 6)
        y = 700
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "2,400ms → 48ms", y, FONT_TITLE, color)
        
        color = lerp_color(COLORS["void"], COLORS["cyan"], alpha)
        draw_centered(draw, "The difference between interruption and intuition", y + 70, FONT_BODY, color, glow=False)
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_technical(progress: float) -> Image.Image:
    """Technical credibility - tests + stack."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Background
    NEURAL_NET.draw(draw, progress, intensity=0.1)
    
    # Title
    draw_glowing_text(draw, "PRODUCTION READY", SAFE_LEFT, SAFE_TOP, FONT_SUBTITLE, COLORS["cyan"])
    
    # Terminal on left
    term_x, term_y = SAFE_LEFT, 180
    term_w, term_h = 750, 420
    
    # Terminal chrome
    draw_neon_box(draw, (term_x, term_y, term_x + term_w, term_y + term_h), COLORS["cyan"], fill=(10, 15, 25))
    draw.rounded_rectangle((term_x, term_y, term_x + term_w, term_y + 35), radius=10, fill=(20, 30, 45))
    
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse((term_x + 15 + i * 22, term_y + 10, term_x + 27 + i * 22, term_y + 22), fill=c)
    
    # Terminal content - animated typing
    lines = [
        ("$ npx vitest run", COLORS["orange"]),
        ("", COLORS["white"]),
        ("✓ flow.engine.test.ts    (6)", COLORS["green"]),
        ("✓ mcp.test.ts           (45)", COLORS["green"]),
        ("✓ store.test.ts        (180)", COLORS["green"]),
        ("✓ cli.test.ts          (156)", COLORS["green"]),
        ("", COLORS["white"]),
        ("Tests:  656 passed", COLORS["cyan"]),
        ("Time:   50.25s", COLORS["ghost"]),
    ]
    
    visible = int(len(lines) * min(progress * 1.3, 1.0))
    for i, (line, color) in enumerate(lines[:visible]):
        ly = term_y + 50 + i * 36
        if line:
            draw.text((term_x + 20, ly), line, font=FONT_MONO, fill=color)
    
    # Tech stack on right - simple list
    if progress > 0.3:
        stack_x = term_x + term_w + 80
        
        stack = [
            ("Qwen3-Embedding-4B", "State-of-art embeddings", COLORS["cyan"]),
            ("Qwen3-Reranker-4B", "Neural reranking", COLORS["purple"]),
            ("SQLite + sqlite-vec", "Hybrid BM25 + vector", COLORS["green"]),
            ("node-llama-cpp", "Native GGUF inference", COLORS["orange"]),
        ]
        
        draw.text((stack_x, 180), "Tech Stack", font=FONT_SUBTITLE, fill=COLORS["white"])
        
        for i, (name, desc, color) in enumerate(stack):
            sp = max(0, min((progress - 0.3 - i * 0.1) * 4, 1.0))
            if sp <= 0:
                continue
            
            y = 250 + i * 100
            alpha = ease_out(sp)
            
            # Bullet
            draw.ellipse([stack_x, y + 8, stack_x + 16, y + 24], 
                        fill=lerp_color(COLORS["void"], color, alpha))
            
            draw.text((stack_x + 30, y), name, font=FONT_BODY, 
                     fill=lerp_color(COLORS["void"], COLORS["white"], alpha))
            draw.text((stack_x + 30, y + 35), desc, font=FONT_SMALL, 
                     fill=lerp_color(COLORS["void"], COLORS["ghost"], alpha))
    
    # Compatibility badges at bottom
    if progress > 0.7:
        alpha = ease_out((progress - 0.7) * 3)
        
        agents = ["Hermes", "Claude Code", "Codex", "Gemini", "Kiro", "VS Code"]
        badge_w = 200
        total_w = len(agents) * badge_w + (len(agents) - 1) * 20
        start_x = (WIDTH - total_w) // 2
        y = 700
        
        draw.text((start_x, y - 40), "Works with:", font=FONT_BODY, 
                 fill=lerp_color(COLORS["void"], COLORS["white"], alpha))
        
        for i, agent in enumerate(agents):
            x = start_x + i * (badge_w + 20)
            ap = max(0, min((progress - 0.75 - i * 0.03) * 8, 1.0))
            
            if ap > 0:
                badge_alpha = ease_out(ap)
                draw_neon_box(draw, (x, y, x + badge_w, y + 50), 
                             lerp_color(COLORS["void"], COLORS["cyan"], badge_alpha))
                
                text_w, _ = get_text_size(agent, FONT_SMALL)
                draw.text((x + (badge_w - text_w) // 2, y + 12), agent, font=FONT_SMALL,
                         fill=lerp_color(COLORS["void"], COLORS["white"], badge_alpha))
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_comparison(progress: float) -> Image.Image:
    """Side-by-side comparison - the money shot."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Background
    draw_hex_grid(draw, progress, 0.04)
    
    # Title
    draw_centered(draw, "THE DIFFERENCE", SAFE_TOP, FONT_SUBTITLE, COLORS["white"], glow=False)
    
    # Two columns
    col_w = 750
    gap = 80
    left_x = (WIDTH - col_w * 2 - gap) // 2
    right_x = left_x + col_w + gap
    col_y = 160
    col_h = 500
    
    # LEFT - Traditional (red theme)
    draw_neon_box(draw, (left_x, col_y, left_x + col_w, col_y + col_h), COLORS["red"])
    draw.text((left_x + 30, col_y + 20), "❌ Traditional RAG", font=FONT_SUBTITLE, fill=COLORS["red"])
    
    left_steps = [
        "User asks question...",
        "Agent: I need to search",
        "→ tool_call: search()",
        "⏳ Waiting 1.2s...",
        "⏳ Reranking 0.8s...",
        "Finally answering...",
    ]
    
    for i, step in enumerate(left_steps):
        sp = max(0, min((progress - i * 0.08) * 3, 1.0))
        if sp > 0:
            color = COLORS["red"] if "⏳" in step or "→" in step else COLORS["ghost"]
            draw.text((left_x + 40, col_y + 80 + i * 55), step, font=FONT_BODY,
                     fill=lerp_color(COLORS["void"], color, ease_out(sp)))
    
    # Timer for left
    if progress > 0.4:
        elapsed = min((progress - 0.4) * 4, 2.4)
        draw_glowing_text(draw, f"{elapsed:.1f}s", left_x + 280, col_y + 420, FONT_TITLE, COLORS["red"])
    
    # RIGHT - FlowState (green theme)
    draw_neon_box(draw, (right_x, col_y, right_x + col_w, col_y + col_h), COLORS["green"])
    draw.text((right_x + 30, col_y + 20), "✓ FlowState-QMD", font=FONT_SUBTITLE, fill=COLORS["green"])
    
    right_steps = [
        "User asks question...",
        "→ intuition.json ready!",
        "  • CHANGELOG.md",
        "  • ADR-017.md",
        "Agent answers instantly",
        "with full context ✓",
    ]
    
    for i, step in enumerate(right_steps):
        sp = max(0, min((progress - i * 0.06) * 4, 1.0))
        if sp > 0:
            if "→" in step or "•" in step:
                color = COLORS["cyan"]
            elif "✓" in step:
                color = COLORS["green"]
            else:
                color = COLORS["white"]
            draw.text((right_x + 40, col_y + 80 + i * 55), step, font=FONT_BODY,
                     fill=lerp_color(COLORS["void"], color, ease_out(sp)))
    
    # Timer for right - instant!
    if progress > 0.3:
        draw_glowing_text(draw, "48ms", right_x + 280, col_y + 420, FONT_TITLE, COLORS["green"])
    
    # VS divider
    vs_y = col_y + col_h // 2 - 20
    draw_glowing_text(draw, "VS", CENTER_X - 30, vs_y, FONT_TITLE, COLORS["white"])
    
    # Bottom verdict
    if progress > 0.85:
        alpha = ease_out((progress - 0.85) * 6)
        y = 730
        
        draw_neon_box(draw, (SAFE_LEFT + 100, y, SAFE_RIGHT - 100, y + 100), COLORS["cyan"])
        
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered(draw, "Context was ready. No search needed.", y + 30, FONT_SUBTITLE, color, glow=False)
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_finale(progress: float) -> Image.Image:
    """Epic finale with the tagline."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Full matrix + neural effect
    intensity = 0.2 + progress * 0.3
    MATRIX.draw(draw, progress, intensity=intensity * 0.6)
    NEURAL_NET.draw(draw, progress, intensity=intensity * 0.4)
    
    # Energy bursts
    if progress > 0.1:
        draw_energy_burst(draw, CENTER_X, CENTER_Y, (progress - 0.1) * 1.5, COLORS["cyan"])
    
    # Main title
    title_alpha = ease_elastic(min(progress * 2, 1.0))
    draw_centered(draw, "FlowState-QMD", 280, FONT_HERO, 
                 lerp_color(COLORS["void"], COLORS["cyan"], title_alpha))
    
    # Tagline
    if progress > 0.25:
        alpha = ease_out((progress - 0.25) * 2)
        draw_centered(draw, "\"Why ask when your agent already knows?\"", 420, FONT_TITLE,
                     lerp_color(COLORS["void"], COLORS["white"], alpha))
    
    # Stats
    if progress > 0.45:
        alpha = ease_out((progress - 0.45) * 2)
        draw_centered(draw, "50x faster  •  89% fewer calls  •  656 tests passing", 540, FONT_BODY,
                     lerp_color(COLORS["void"], COLORS["ghost"], alpha))
    
    # GitHub
    if progress > 0.6:
        alpha = ease_out((progress - 0.6) * 2.5)
        
        box_w = 600
        box_x = (WIDTH - box_w) // 2
        draw_neon_box(draw, (box_x, 620, box_x + box_w, 700), COLORS["cyan"])
        draw_centered(draw, "github.com/amanning3390/flowstate-qmd", 642, FONT_BODY,
                     lerp_color(COLORS["void"], COLORS["white"], alpha), glow=False)
    
    # Hackathon badge
    if progress > 0.75:
        alpha = ease_out((progress - 0.75) * 4)
        
        badge_w = 400
        badge_x = (WIDTH - badge_w) // 2
        draw_neon_box(draw, (badge_x, 760, badge_x + badge_w, 830), COLORS["purple"])
        draw_centered(draw, "🏆 Hermes Hackathon 2026", 778, FONT_BODY,
                     lerp_color(COLORS["void"], COLORS["white"], alpha), glow=False)
    
    draw_scan_lines(draw, 0.03)
    return img


def scene_credits(progress: float) -> Image.Image:
    """Quick credits with fade out."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Fading matrix
    intensity = max(0, 0.15 - progress * 0.15)
    MATRIX.draw(draw, progress, intensity=intensity)
    
    alpha = ease_out(min(progress * 2, 1.0))
    if progress > 0.7:
        alpha *= 1 - (progress - 0.7) / 0.3  # Fade out
    
    draw_centered(draw, "Built on @tobi/qmd", 380, FONT_BODY, 
                 lerp_color(COLORS["void"], COLORS["ghost"], alpha), glow=False)
    draw_centered(draw, "FlowState by Adam Manning", 450, FONT_TITLE,
                 lerp_color(COLORS["void"], COLORS["white"], alpha), glow=False)
    draw_centered(draw, "Powered by Qwen3 • SQLite-vec • node-llama-cpp", 540, FONT_SMALL,
                 lerp_color(COLORS["void"], COLORS["dim"], alpha), glow=False)
    
    return img


# === TIMELINE ===
SCENES = [
    ("intro", 6.0, scene_intro),
    ("problem", 9.0, scene_problem),
    ("transition", 5.0, scene_transition),
    ("solution", 10.0, scene_solution),
    ("metrics", 10.0, scene_metrics),
    ("technical", 10.0, scene_technical),
    ("comparison", 12.0, scene_comparison),
    ("finale", 10.0, scene_finale),
    ("credits", 6.0, scene_credits),
]

TOTAL_DURATION = sum(d for _, d, _ in SCENES)
print(f"Total video duration: {TOTAL_DURATION}s")


# === RENDER ===
def render_all_frames():
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    
    frame_idx = 0
    for name, duration, fn in SCENES:
        frames = int(duration * FPS)
        print(f"Rendering {name} ({frames} frames)...")
        for i in range(frames):
            progress = i / max(frames - 1, 1)
            frame = fn(progress)
            frame.save(FRAMES_DIR / f"frame_{frame_idx:05d}.png", "PNG")
            frame_idx += 1
            if i % 30 == 0:
                print(f"  {i}/{frames}")
    print(f"Total: {frame_idx} frames")


def encode_video():
    print("Encoding...")
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "slow", "-crf", "18", "-movflags", "+faststart",
        str(OUTPUT)
    ]
    subprocess.run(cmd, check=True)
    print(f"Wrote {OUTPUT}")


def main():
    print("=" * 60)
    print("FlowState-QMD - NEURAL MATRIX EDITION")
    print("=" * 60)
    render_all_frames()
    encode_video()
    shutil.rmtree(FRAMES_DIR)
    
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\n✓ {OUTPUT}")
    print(f"  {TOTAL_DURATION}s | {WIDTH}x{HEIGHT} | {size_mb:.1f}MB")


if __name__ == "__main__":
    main()
