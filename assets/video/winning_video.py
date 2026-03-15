#!/usr/bin/env python3
"""
FlowState-QMD Hackathon Winning Video Generator

Design principles:
1. Hook in first 3 seconds - dramatic visual + bold claim
2. Show the pain viscerally - make judges feel the stutter
3. Reveal solution cinematically - the "aha" moment
4. Prove it with data - animated metrics
5. Technical credibility without boring
6. Emotional close - memorable tagline

FIXES:
- All text properly bounded within safe margins
- Slower scene pacing for readability
- Correct hardware: Apple M4 / 24GB

Target: 90 seconds, 1080p, 30fps
"""

import math
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# === CONFIG ===
WIDTH, HEIGHT = 1920, 1080
FPS = 30
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT = SCRIPT_DIR / "flowstate_winning.mp4"
FRAMES_DIR = SCRIPT_DIR / "winning_frames"

# Safe margins - keep all text within these bounds
MARGIN_LEFT = 120
MARGIN_RIGHT = 120
MARGIN_TOP = 80
MARGIN_BOTTOM = 80
SAFE_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 1680px usable
SAFE_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM  # 920px usable

# === CINEMATIC COLOR PALETTE ===
COLORS = {
    # Backgrounds - deep space feel
    "void": (4, 6, 14),
    "deep": (8, 12, 24),
    "midnight": (12, 18, 36),
    
    # Accent colors - vibrant and modern
    "electric": (0, 240, 200),      # Cyan-green (primary accent)
    "plasma": (120, 80, 255),        # Purple
    "solar": (255, 180, 50),         # Warm gold
    "danger": (255, 75, 85),         # Alert red
    "success": (50, 220, 130),       # Success green
    
    # Text
    "white": (255, 255, 255),
    "ghost": (180, 190, 210),
    "muted": (100, 115, 140),
    
    # UI elements
    "glass": (20, 30, 50),
    "border": (40, 55, 85),
}

# === FONTS ===
def load_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """Load system fonts with fallbacks."""
    paths = {
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ],
        "regular": [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ],
        "mono": [
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Monaco.ttf",
        ],
    }
    for path in paths.get(weight, paths["regular"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_HERO = load_font(100, "bold")      # Reduced from 120
FONT_TITLE = load_font(64, "bold")      # Reduced from 72
FONT_SUBTITLE = load_font(38, "bold")   # Reduced from 42
FONT_BODY = load_font(32, "regular")    # Reduced from 36
FONT_SMALL = load_font(26, "regular")   # Reduced from 28
FONT_MONO = load_font(28, "mono")       # Reduced from 32
FONT_MONO_SMALL = load_font(22, "mono") # Reduced from 24
FONT_METRIC = load_font(80, "bold")     # Reduced from 96
FONT_METRIC_LABEL = load_font(28, "regular")

# === DRAWING UTILITIES ===

def ease_out_cubic(t: float) -> float:
    """Smooth deceleration curve."""
    return 1 - pow(1 - t, 3)

def ease_in_out_cubic(t: float) -> float:
    """Smooth acceleration and deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t: float) -> float:
    """Bouncy overshoot effect."""
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t

def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Interpolate between two colors."""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def draw_gradient_bg(img: Image.Image, progress: float = 0, style: str = "default"):
    """Draw an animated gradient background."""
    draw = ImageDraw.Draw(img)
    
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        
        if style == "danger":
            wave = (math.sin(progress * math.pi * 2 + ratio * 4) + 1) / 2
            base = lerp_color(COLORS["void"], (20, 8, 12), ratio)
            color = lerp_color(base, (30, 12, 18), wave * 0.3)
        elif style == "success":
            wave = (math.sin(progress * math.pi * 2 + ratio * 4) + 1) / 2
            base = lerp_color(COLORS["void"], (8, 20, 16), ratio)
            color = lerp_color(base, (12, 30, 24), wave * 0.3)
        else:
            wave = (math.sin(progress * math.pi * 2 + ratio * 6) + 1) / 2
            base = lerp_color(COLORS["void"], COLORS["deep"], ratio)
            color = lerp_color(base, COLORS["midnight"], wave * 0.2)
        
        draw.line([(0, y), (WIDTH, y)], fill=color)

def draw_particles(draw: ImageDraw.ImageDraw, progress: float, count: int = 30, color: tuple = None):
    """Draw floating particle effect."""
    color = color or COLORS["electric"]
    for i in range(count):
        seed = i * 7919
        x = ((seed * 13) % WIDTH + progress * 50 * ((i % 3) + 1)) % WIDTH
        y = ((seed * 17) % HEIGHT + progress * 30 * ((i % 2) + 1)) % HEIGHT
        size = (seed % 4) + 1
        alpha = 0.3 + 0.4 * ((seed % 100) / 100)
        c = lerp_color(COLORS["void"], color, alpha)
        draw.ellipse([x, y, x + size, y + size], fill=c)

def draw_scan_line(draw: ImageDraw.ImageDraw, y: int, color: tuple, width: int = 3):
    """Draw a horizontal scan line effect."""
    for offset in range(-20, 21):
        alpha = 1 - abs(offset) / 20
        c = lerp_color(COLORS["void"], color, alpha * 0.5)
        draw.line([(0, y + offset), (WIDTH, y + offset)], fill=c, width=1)
    draw.line([(0, y), (WIDTH, y)], fill=color, width=width)

def draw_glass_panel(draw: ImageDraw.ImageDraw, box: tuple, highlight: tuple = None):
    """Draw a frosted glass panel."""
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=16, fill=COLORS["glass"], outline=COLORS["border"], width=2)
    if highlight:
        draw.rounded_rectangle((x1, y1, x2, y1 + 4), radius=2, fill=highlight)

def draw_progress_bar(draw: ImageDraw.ImageDraw, box: tuple, progress: float, color: tuple, label: str = None):
    """Draw an animated progress bar."""
    x1, y1, x2, y2 = box
    width = x2 - x1
    
    draw.rounded_rectangle(box, radius=8, fill=COLORS["glass"], outline=COLORS["border"], width=1)
    
    fill_width = int(width * min(progress, 1.0))
    if fill_width > 0:
        draw.rounded_rectangle((x1, y1, x1 + fill_width, y2), radius=8, fill=color)
    
    if label:
        draw.text((x1 + 10, y1 + 5), label, font=FONT_SMALL, fill=COLORS["white"])

def draw_terminal(draw: ImageDraw.ImageDraw, x1: int, y1: int, width: int, height: int, lines: list, typing_progress: float = 1.0):
    """Draw a realistic terminal window."""
    x2 = x1 + width
    y2 = y1 + height
    
    # Window chrome
    draw.rounded_rectangle((x1, y1, x2, y2), radius=12, fill=(15, 18, 25), outline=COLORS["border"], width=2)
    draw.rounded_rectangle((x1, y1, x2, y1 + 32), radius=12, fill=(25, 30, 40))
    
    # Traffic lights
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (39, 201, 63)]):
        cx = x1 + 18 + i * 20
        draw.ellipse((cx, y1 + 10, cx + 12, y1 + 22), fill=c)
    
    # Terminal content
    line_height = 28
    visible_lines = int(len(lines) * typing_progress) + 1
    
    for i, line in enumerate(lines[:visible_lines]):
        ly = y1 + 44 + i * line_height
        if ly > y2 - 20:
            break
        
        if line.startswith("$") or line.startswith(">"):
            color = COLORS["solar"]
        elif line.startswith("✓") or "passed" in line.lower():
            color = COLORS["success"]
        elif line.startswith("✗") or "error" in line.lower():
            color = COLORS["danger"]
        elif line.startswith("#"):
            color = COLORS["muted"]
        else:
            color = COLORS["ghost"]
        
        draw.text((x1 + 16, ly), line, font=FONT_MONO_SMALL, fill=color)

def get_text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    """Get text width."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, color: tuple):
    """Draw horizontally centered text within safe area."""
    w = get_text_width(text, font)
    x = MARGIN_LEFT + (SAFE_WIDTH - w) // 2
    draw.text((x, y), text, font=font, fill=color)

def draw_text_safe(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, color: tuple, max_width: int = None):
    """Draw text ensuring it stays within safe margins."""
    # Clamp x to safe area
    x = max(MARGIN_LEFT, min(x, WIDTH - MARGIN_RIGHT - 100))
    y = max(MARGIN_TOP, min(y, HEIGHT - MARGIN_BOTTOM - 50))
    draw.text((x, y), text, font=font, fill=color)

def draw_metric_card(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, label: str, color: tuple, animate: float = 1.0):
    """Draw an animated metric card."""
    card_width = 360
    card_height = 160
    
    # Ensure card stays in bounds
    x = max(MARGIN_LEFT, min(x, WIDTH - MARGIN_RIGHT - card_width))
    y = max(MARGIN_TOP, min(y, HEIGHT - MARGIN_BOTTOM - card_height))
    
    draw_glass_panel(draw, (x, y, x + card_width, y + card_height), color)
    
    # Value with animation
    if animate < 1.0:
        try:
            num = float(value.replace("x", "").replace("%", "").replace("ms", "").replace("s", ""))
            displayed = int(num * ease_out_cubic(animate))
            suffix = "x" if "x" in value else ("%" if "%" in value else ("ms" if "ms" in value else ""))
            value = f"{displayed}{suffix}"
        except:
            pass
    
    draw.text((x + 24, y + 24), value, font=FONT_METRIC, fill=color)
    draw.text((x + 24, y + 115), label, font=FONT_METRIC_LABEL, fill=COLORS["ghost"])


# === SCENE GENERATORS ===

def scene_hook(progress: float) -> Image.Image:
    """
    Scene 1: The Hook (0-5s)
    Dramatic opening that grabs attention.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress)
    draw_particles(draw, progress, 40, COLORS["plasma"])
    
    # Animated reveal - SLOWER
    if progress > 0.1:
        alpha = ease_out_cubic(min((progress - 0.1) * 2, 1.0))
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered_text(draw, "What if your AI", 320, FONT_TITLE, color)
    
    if progress > 0.35:
        alpha = ease_out_cubic(min((progress - 0.35) * 2, 1.0))
        color = lerp_color(COLORS["void"], COLORS["electric"], alpha)
        draw_centered_text(draw, "already knew the answer", 420, FONT_HERO, color)
    
    if progress > 0.6:
        alpha = ease_out_cubic(min((progress - 0.6) * 2, 1.0))
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered_text(draw, "before it decided to search?", 560, FONT_TITLE, color)
    
    # Scan line effect
    if progress > 0.5:
        scan_y = int(300 + (progress - 0.5) * 600)
        draw_scan_line(draw, scan_y, COLORS["electric"])
    
    return img


def scene_problem_setup(progress: float) -> Image.Image:
    """
    Scene 2: The Problem Setup (5-12s)
    Show the traditional RAG pain point - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress, "danger")
    draw_particles(draw, progress, 20, COLORS["danger"])
    
    # Title - within safe margins
    draw_text_safe(draw, "THE STUTTER LOOP", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["danger"])
    draw_text_safe(draw, "Every AI agent's hidden bottleneck", MARGIN_LEFT, MARGIN_TOP + 50, FONT_BODY, COLORS["ghost"])
    
    # Timeline - properly bounded
    steps = [
        ("User asks question", COLORS["white"]),
        ("Agent realizes context missing", COLORS["solar"]),
        ("Agent formulates search", COLORS["solar"]),
        ("Execute retrieval tool", COLORS["danger"]),
        ("Wait for search + rerank", COLORS["danger"]),
        ("Process results", COLORS["danger"]),
        ("Finally answer...", COLORS["muted"]),
    ]
    
    timeline_x = MARGIN_LEFT + 40
    timeline_y = 200
    step_height = 75
    
    # Slower reveal - one step every ~0.12 progress
    visible_steps = min(int(progress * 10) + 1, len(steps))
    
    for i, (step, color) in enumerate(steps[:visible_steps]):
        y = timeline_y + i * step_height
        
        # Connection line
        if i > 0:
            draw.line([(timeline_x + 15, y - step_height + 35), (timeline_x + 15, y + 5)], fill=COLORS["border"], width=2)
        
        # Step circle
        draw.ellipse((timeline_x, y + 5, timeline_x + 30, y + 35), fill=color, outline=COLORS["white"], width=2)
        draw.text((timeline_x + 8, y + 8), str(i + 1), font=FONT_SMALL, fill=COLORS["void"])
        
        # Step text
        draw_text_safe(draw, step, timeline_x + 50, y + 8, FONT_BODY, color)
        
        # Time indicator for slow steps
        if "Wait" in step or "retrieval" in step.lower():
            draw_text_safe(draw, "⏱ 800ms+", timeline_x + 550, y + 8, FONT_BODY, COLORS["danger"])
    
    # Total time callout - bounded on right side
    if progress > 0.75:
        alpha = ease_out_cubic((progress - 0.75) * 4)
        box_x = WIDTH - MARGIN_RIGHT - 500
        box_color = lerp_color(COLORS["void"], COLORS["danger"], alpha * 0.3)
        draw.rounded_rectangle((box_x, 280, box_x + 480, 480), radius=20, fill=box_color, outline=COLORS["danger"], width=3)
        
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw.text((box_x + 30, 310), "Total Latency", font=FONT_SUBTITLE, fill=color)
        
        color = lerp_color(COLORS["void"], COLORS["danger"], alpha)
        draw.text((box_x + 30, 365), "2-4 seconds", font=FONT_HERO, fill=color)
        draw.text((box_x + 30, 450), "per question", font=FONT_BODY, fill=lerp_color(COLORS["void"], COLORS["ghost"], alpha))
    
    return img


def scene_problem_impact(progress: float) -> Image.Image:
    """
    Scene 3: Problem Impact (12-18s)
    Make the pain visceral with a real example - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress, "danger")
    
    # Title
    draw_text_safe(draw, "REACTIVE RAG IN ACTION", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["danger"])
    
    # User message - bounded panel
    panel_width = 1200
    draw_glass_panel(draw, (MARGIN_LEFT, 150, MARGIN_LEFT + panel_width, 230))
    draw.text((MARGIN_LEFT + 20, 168), "User:", font=FONT_BODY, fill=COLORS["electric"])
    draw.text((MARGIN_LEFT + 110, 168), "\"Why did we revert the auth migration?\"", font=FONT_BODY, fill=COLORS["white"])
    
    # Agent thinking stages - SLOWER (one every ~0.15 progress)
    stages = [
        (0.08, "🤔  Thinking...", COLORS["muted"]),
        (0.22, "🔍  I should search for this information...", COLORS["solar"]),
        (0.38, "⚙️   Calling search tool...", COLORS["solar"]),
        (0.54, "⏳  Waiting for results... (1.2s)", COLORS["danger"]),
        (0.70, "📄  Processing 12 results... (0.8s)", COLORS["danger"]),
        (0.85, "✓   Found relevant context", COLORS["success"]),
    ]
    
    y = 270
    for threshold, text, color in stages:
        if progress > threshold:
            alpha = ease_out_cubic(min((progress - threshold) * 3, 1.0))
            c = lerp_color(COLORS["void"], color, alpha)
            draw_text_safe(draw, text, MARGIN_LEFT + 40, y, FONT_BODY, c)
            y += 60
    
    # Timer visualization - bounded on right
    elapsed = min(progress * 3.5, 3.2)
    timer_text = f"{elapsed:.1f}s"
    
    timer_x = WIDTH - MARGIN_RIGHT - 280
    draw_glass_panel(draw, (timer_x, 200, timer_x + 260, 380), COLORS["danger"])
    draw.text((timer_x + 30, 220), "Elapsed", font=FONT_BODY, fill=COLORS["ghost"])
    draw.text((timer_x + 25, 280), timer_text, font=FONT_HERO, fill=COLORS["danger"])
    
    # Bottom callout - centered, bounded
    if progress > 0.88:
        alpha = ease_out_cubic((progress - 0.88) * 8)
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered_text(draw, "This happens every. single. question.", 720, FONT_TITLE, color)
        
        color = lerp_color(COLORS["void"], COLORS["danger"], alpha)
        draw_centered_text(draw, "Flow State: broken.", 810, FONT_SUBTITLE, color)
    
    return img


def scene_solution_reveal(progress: float) -> Image.Image:
    """
    Scene 4: Solution Reveal (18-25s)
    The dramatic "aha" moment - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Transition from red to green
    style = "danger" if progress < 0.25 else "success"
    draw_gradient_bg(img, progress, style)
    
    if progress < 0.25:
        alpha = ease_out_cubic(progress * 4)
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered_text(draw, "But what if...", 480, FONT_TITLE, color)
    
    elif progress < 0.4:
        # Flash transition
        flash = 1 - (progress - 0.25) * 6
        if flash > 0:
            overlay = Image.new("RGB", (WIDTH, HEIGHT), COLORS["electric"])
            img = Image.blend(img, overlay, min(flash * 0.5, 1.0))
            draw = ImageDraw.Draw(img)
    
    else:
        # Reveal FlowState
        draw_particles(draw, progress, 50, COLORS["electric"])
        
        reveal = ease_out_elastic(min((progress - 0.4) * 1.8, 1.0))
        
        y_offset = int((1 - reveal) * 80)
        color = lerp_color(COLORS["void"], COLORS["electric"], reveal)
        draw_centered_text(draw, "FlowState-QMD", 220 + y_offset, FONT_HERO, color)
        
        color = lerp_color(COLORS["void"], COLORS["white"], reveal)
        draw_centered_text(draw, "Anticipatory Memory for AI Agents", 360 + y_offset, FONT_SUBTITLE, color)
        
        # Key insight - bounded panel
        if progress > 0.65:
            alpha = ease_out_cubic((progress - 0.65) * 3)
            
            panel_x = MARGIN_LEFT + 50
            panel_width = SAFE_WIDTH - 100
            draw_glass_panel(draw, (panel_x, 480, panel_x + panel_width, 720), COLORS["electric"])
            
            color = lerp_color(COLORS["void"], COLORS["white"], alpha)
            draw_centered_text(draw, "Context is pre-loaded into memory", 520, FONT_TITLE, color)
            
            color = lerp_color(COLORS["void"], COLORS["electric"], alpha)
            draw_centered_text(draw, "BEFORE the agent starts its turn", 610, FONT_TITLE, color)
            
            color = lerp_color(COLORS["void"], COLORS["ghost"], alpha)
            draw_centered_text(draw, "Zero tool calls. Zero stutter. Zero waiting.", 690, FONT_BODY, color)
    
    return img


def scene_how_it_works(progress: float) -> Image.Image:
    """
    Scene 5: How It Works (25-36s)
    Visual explanation of the architecture - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress, "success")
    draw_particles(draw, progress, 30, COLORS["electric"])
    
    draw_text_safe(draw, "HOW FLOWSTATE WORKS", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["electric"])
    
    # Three-column architecture - bounded
    columns = [
        {
            "title": "1. WATCH",
            "color": COLORS["plasma"],
            "items": ["Monitor agent session", "fs.watch + debounce", "Track last 8KB context"],
            "icon": "👁️"
        },
        {
            "title": "2. ANTICIPATE",
            "color": COLORS["electric"],
            "items": ["Vectorize context", "Query project memory", "Pre-fetch top 3 memories"],
            "icon": "🧠"
        },
        {
            "title": "3. INJECT",
            "color": COLORS["success"],
            "items": ["Write intuition.json", "Agent reads at turn start", "Context already present"],
            "icon": "⚡"
        },
    ]
    
    col_width = 480
    col_gap = 60
    start_x = MARGIN_LEFT + 30
    
    for i, col in enumerate(columns):
        # SLOWER staggered reveal
        col_progress = max(0, min((progress - i * 0.18) * 1.5, 1.0))
        if col_progress <= 0:
            continue
        
        alpha = ease_out_cubic(col_progress)
        x = start_x + i * (col_width + col_gap)
        
        # Column panel
        panel_color = lerp_color(COLORS["void"], col["color"], alpha * 0.15)
        draw.rounded_rectangle((x, 170, x + col_width, 620), radius=20, 
                               fill=panel_color, outline=lerp_color(COLORS["void"], col["color"], alpha), width=2)
        
        # Icon and title
        draw.text((x + 24, 195), col["icon"], font=FONT_HERO, fill=lerp_color(COLORS["void"], col["color"], alpha))
        draw.text((x + 130, 215), col["title"], font=FONT_SUBTITLE, fill=lerp_color(COLORS["void"], col["color"], alpha))
        
        # Items - SLOWER
        for j, item in enumerate(col["items"]):
            item_progress = max(0, min((col_progress - 0.35 - j * 0.12) * 2.5, 1.0))
            if item_progress > 0:
                y = 330 + j * 85
                item_alpha = ease_out_cubic(item_progress)
                
                draw.ellipse((x + 24, y + 6, x + 40, y + 22), 
                            fill=lerp_color(COLORS["void"], col["color"], item_alpha))
                draw.text((x + 54, y), item, font=FONT_BODY, 
                         fill=lerp_color(COLORS["void"], COLORS["white"], item_alpha))
    
    # Arrows between columns
    if progress > 0.55:
        arrow_alpha = ease_out_cubic((progress - 0.55) * 2)
        arrow_color = lerp_color(COLORS["void"], COLORS["electric"], arrow_alpha)
        
        # Arrow 1
        ax1 = start_x + col_width + 15
        draw.polygon([(ax1 + 30, 400), (ax1 + 45, 420), (ax1 + 30, 440)], fill=arrow_color)
        draw.line([(ax1, 420), (ax1 + 30, 420)], fill=arrow_color, width=4)
        
        # Arrow 2
        ax2 = start_x + 2 * (col_width + col_gap) - 45
        draw.polygon([(ax2 + 30, 400), (ax2 + 45, 420), (ax2 + 30, 440)], fill=arrow_color)
        draw.line([(ax2, 420), (ax2 + 30, 420)], fill=arrow_color, width=4)
    
    # Bottom result - bounded
    if progress > 0.8:
        alpha = ease_out_cubic((progress - 0.8) * 5)
        
        draw_text_safe(draw, "Result:", MARGIN_LEFT, 700, FONT_BODY, lerp_color(COLORS["void"], COLORS["white"], alpha))
        
        # Before bar
        draw_text_safe(draw, "Before:", MARGIN_LEFT, 750, FONT_SMALL, lerp_color(COLORS["void"], COLORS["danger"], alpha))
        draw_progress_bar(draw, (MARGIN_LEFT + 100, 752, MARGIN_LEFT + 700, 782), 1.0, 
                         lerp_color(COLORS["void"], COLORS["danger"], alpha * 0.7), "2400ms")
        
        # After bar
        draw_text_safe(draw, "After:", MARGIN_LEFT, 810, FONT_SMALL, lerp_color(COLORS["void"], COLORS["success"], alpha))
        draw_progress_bar(draw, (MARGIN_LEFT + 100, 812, MARGIN_LEFT + 700, 842), 0.02, 
                         lerp_color(COLORS["void"], COLORS["success"], alpha * 0.7), "48ms")
    
    return img


def scene_metrics(progress: float) -> Image.Image:
    """
    Scene 6: The Metrics (36-46s)
    Animated performance metrics - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress, "success")
    draw_particles(draw, progress, 40, COLORS["success"])
    
    draw_text_safe(draw, "MEASURED RESULTS", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["electric"])
    draw_text_safe(draw, "Benchmarked on 5,000-document knowledge base, Apple M4, 24GB", MARGIN_LEFT, MARGIN_TOP + 50, FONT_BODY, COLORS["ghost"])
    
    # Metric cards - SLOWER staggered animation, bounded
    metrics = [
        ("50x", "Faster first-turn", COLORS["electric"], 0.0),
        ("89%", "Fewer tool calls", COLORS["success"], 0.18),
        ("73%", "Cache hit rate", COLORS["plasma"], 0.36),
        ("48ms", "Avg latency", COLORS["solar"], 0.54),
    ]
    
    card_width = 360
    card_height = 160
    cards_per_row = 2
    h_gap = (SAFE_WIDTH - cards_per_row * card_width) // (cards_per_row + 1)
    v_gap = 60
    
    for i, (value, label, color, delay) in enumerate(metrics):
        metric_progress = max(0, min((progress - delay) * 1.5, 1.0))
        if metric_progress <= 0:
            continue
        
        row = i // cards_per_row
        col = i % cards_per_row
        x = MARGIN_LEFT + h_gap + col * (card_width + h_gap)
        y = 220 + row * (card_height + v_gap)
        
        y_offset = int((1 - ease_out_cubic(metric_progress)) * 40)
        draw_metric_card(draw, x, y + y_offset, value, label, color, metric_progress)
    
    # Comparison callout - bounded
    if progress > 0.75:
        alpha = ease_out_cubic((progress - 0.75) * 4)
        
        panel_x = MARGIN_LEFT + 50
        panel_width = SAFE_WIDTH - 100
        draw.rounded_rectangle((panel_x, 700, panel_x + panel_width, 840), radius=20, 
                               fill=lerp_color(COLORS["void"], COLORS["glass"], alpha),
                               outline=lerp_color(COLORS["void"], COLORS["electric"], alpha), width=2)
        
        color = lerp_color(COLORS["void"], COLORS["white"], alpha)
        draw_centered_text(draw, "Traditional RAG: 2,400ms  →  FlowState: 48ms", 730, FONT_TITLE, color)
        
        color = lerp_color(COLORS["void"], COLORS["electric"], alpha)
        draw_centered_text(draw, "The difference between interruption and intuition.", 800, FONT_BODY, color)
    
    return img


def scene_technical_proof(progress: float) -> Image.Image:
    """
    Scene 7: Technical Proof (46-56s)
    Show real code/terminal - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress)
    
    draw_text_safe(draw, "REAL. TESTED. PRODUCTION-READY.", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["electric"])
    
    # Terminal - bounded
    terminal_lines = [
        "$ npx vitest run",
        "",
        "✓ test/flow.engine.test.ts (6 tests)",
        "✓ test/mcp.test.ts (45 tests)",
        "✓ test/store.test.ts (180 tests)",
        "✓ test/cli.test.ts (156 tests)",
        "",
        "Test Files:  17 passed (17)",
        "Tests:       656 passed",
        "Duration:    50.25s",
    ]
    
    typing = min(progress * 1.2, 1.0)
    draw_terminal(draw, MARGIN_LEFT, 150, 800, 400, terminal_lines, typing_progress=typing)
    
    # Tech stack cards - bounded on right
    if progress > 0.25:
        stack_alpha = ease_out_cubic((progress - 0.25) * 1.5)
        
        stack = [
            ("Qwen3-Embedding-4B", "Local embeddings"),
            ("Qwen3-Reranker-4B", "Neural reranking"),
            ("SQLite + sqlite-vec", "Hybrid search"),
            ("node-llama-cpp", "GGUF inference"),
        ]
        
        card_x = WIDTH - MARGIN_RIGHT - 520
        for i, (tech, desc) in enumerate(stack):
            y = 160 + i * 90
            
            item_alpha = stack_alpha * max(0, min((progress - 0.25 - i * 0.1) * 4, 1.0))
            
            draw_glass_panel(draw, (card_x, y, card_x + 500, y + 78))
            draw.text((card_x + 20, y + 12), tech, font=FONT_BODY, 
                     fill=lerp_color(COLORS["void"], COLORS["electric"], item_alpha))
            draw.text((card_x + 20, y + 46), desc, font=FONT_SMALL, 
                     fill=lerp_color(COLORS["void"], COLORS["ghost"], item_alpha))
    
    # MCP compatibility - bounded at bottom
    if progress > 0.6:
        alpha = ease_out_cubic((progress - 0.6) * 2)
        
        draw_text_safe(draw, "Works with:", MARGIN_LEFT, 600, FONT_BODY, lerp_color(COLORS["void"], COLORS["white"], alpha))
        
        agents = ["Hermes", "Claude Code", "Codex", "Gemini", "Kiro", "VS Code"]
        agent_width = 240
        agent_gap = 30
        
        for i, agent in enumerate(agents):
            x = MARGIN_LEFT + i * (agent_width + agent_gap)
            if x + agent_width > WIDTH - MARGIN_RIGHT:
                break  # Don't overflow
            
            agent_alpha = alpha * max(0, min((progress - 0.65 - i * 0.04) * 8, 1.0))
            
            draw.rounded_rectangle((x, 660, x + agent_width, 720), radius=10,
                                   fill=lerp_color(COLORS["void"], COLORS["glass"], agent_alpha),
                                   outline=lerp_color(COLORS["void"], COLORS["electric"], agent_alpha), width=2)
            draw.text((x + 15, 673), agent, font=FONT_BODY, 
                     fill=lerp_color(COLORS["void"], COLORS["white"], agent_alpha))
    
    return img


def scene_demo_flow(progress: float) -> Image.Image:
    """
    Scene 8: Demo Flow (56-68s)
    Side-by-side comparison - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress, "success")
    
    draw_text_safe(draw, "THE FLOWSTATE EXPERIENCE", MARGIN_LEFT, MARGIN_TOP, FONT_SUBTITLE, COLORS["electric"])
    
    # Column positions - properly bounded
    left_x = MARGIN_LEFT
    right_x = WIDTH // 2 + 40
    col_width = (WIDTH - MARGIN_LEFT - MARGIN_RIGHT - 80) // 2
    
    # LEFT: Traditional (slow)
    draw_text_safe(draw, "❌ Traditional RAG", left_x, 140, FONT_BODY, COLORS["danger"])
    
    trad_steps = [
        (0.0, "User: Why did we revert auth?"),
        (0.12, "Agent: [thinking...]"),
        (0.24, "Agent: I should search..."),
        (0.36, "→ search(\"auth revert\")"),
        (0.52, "⏳ Waiting 2.1 seconds..."),
        (0.72, "Agent: Based on results..."),
    ]
    
    for i, (threshold, text) in enumerate(trad_steps):
        if progress > threshold:
            alpha = ease_out_cubic(min((progress - threshold) * 3, 1.0))
            color = COLORS["danger"] if "⏳" in text or "→" in text else COLORS["ghost"]
            # Truncate if needed to fit
            if len(text) > 35:
                text = text[:32] + "..."
            draw_text_safe(draw, text, left_x + 20, 200 + i * 55, FONT_SMALL, lerp_color(COLORS["void"], color, alpha))
    
    # RIGHT: FlowState (instant)
    draw_text_safe(draw, "✓ FlowState-QMD", right_x, 140, FONT_BODY, COLORS["success"])
    
    flow_steps = [
        (0.0, "User: Why did we revert auth?"),
        (0.10, "→ intuition.json already has:"),
        (0.18, "  • CHANGELOG.md#auth-rollback"),
        (0.26, "  • ADR-017.md"),
        (0.36, "Agent: The auth migration was"),
        (0.44, "reverted on March 3rd due to"),
        (0.52, "connection pool exhaustion..."),
    ]
    
    for i, (threshold, text) in enumerate(flow_steps):
        if progress > threshold:
            alpha = ease_out_cubic(min((progress - threshold) * 3, 1.0))
            if "→" in text or "•" in text:
                color = COLORS["electric"]
            elif "Agent:" in text:
                color = COLORS["success"]
            else:
                color = COLORS["white"]
            draw_text_safe(draw, text, right_x + 20, 200 + i * 55, FONT_SMALL, lerp_color(COLORS["void"], color, alpha))
    
    # Timer comparison - bounded
    if progress > 0.55:
        alpha = ease_out_cubic((progress - 0.55) * 2)
        
        elapsed_left = min((progress - 0.1) * 3, 2.4)
        draw.text((left_x + 100, 600), f"{elapsed_left:.1f}s", font=FONT_METRIC, 
                 fill=lerp_color(COLORS["void"], COLORS["danger"], alpha))
        
        draw.text((right_x + 100, 600), "48ms", font=FONT_METRIC, 
                 fill=lerp_color(COLORS["void"], COLORS["success"], alpha))
    
    # Verdict - bounded panel
    if progress > 0.82:
        alpha = ease_out_cubic((progress - 0.82) * 5)
        
        panel_x = MARGIN_LEFT + 100
        panel_width = SAFE_WIDTH - 200
        draw_glass_panel(draw, (panel_x, 750, panel_x + panel_width, 870), COLORS["electric"])
        
        draw_centered_text(draw, "The agent answered from memory.", 780, FONT_TITLE, 
                          lerp_color(COLORS["void"], COLORS["white"], alpha))
        draw_centered_text(draw, "No search needed. No waiting. Pure flow.", 840, FONT_BODY, 
                          lerp_color(COLORS["void"], COLORS["electric"], alpha))
    
    return img


def scene_tagline(progress: float) -> Image.Image:
    """
    Scene 9: Tagline & Close (68-78s)
    Memorable ending - SLOWER.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress)
    draw_particles(draw, progress, 60, COLORS["electric"])
    
    reveal = ease_out_elastic(min(progress * 1.2, 1.0))
    
    # Main title
    y_offset = int((1 - reveal) * 80)
    draw_centered_text(draw, "FlowState-QMD", 260 + y_offset, FONT_HERO, 
                      lerp_color(COLORS["void"], COLORS["electric"], reveal))
    
    # Tagline
    if progress > 0.2:
        tag_alpha = ease_out_cubic((progress - 0.2) * 1.5)
        draw_centered_text(draw, "\"Why ask when your agent already knows?\"", 400, FONT_TITLE, 
                          lerp_color(COLORS["void"], COLORS["white"], tag_alpha))
    
    # Key stats
    if progress > 0.4:
        stats_alpha = ease_out_cubic((progress - 0.4) * 1.5)
        draw_centered_text(draw, "50x faster  •  89% fewer tool calls  •  656 tests passing", 520, FONT_BODY, 
                          lerp_color(COLORS["void"], COLORS["ghost"], stats_alpha))
    
    # GitHub link - bounded panel
    if progress > 0.55:
        link_alpha = ease_out_cubic((progress - 0.55) * 2)
        
        panel_width = 600
        panel_x = (WIDTH - panel_width) // 2
        draw_glass_panel(draw, (panel_x, 620, panel_x + panel_width, 700), COLORS["electric"])
        draw_centered_text(draw, "github.com/amanning3390/flowstate-qmd", 642, FONT_BODY, 
                          lerp_color(COLORS["void"], COLORS["white"], link_alpha))
    
    # Hackathon badge
    if progress > 0.72:
        badge_alpha = ease_out_cubic((progress - 0.72) * 3)
        
        badge_width = 360
        badge_x = (WIDTH - badge_width) // 2
        draw.rounded_rectangle((badge_x, 780, badge_x + badge_width, 850), radius=15,
                               fill=lerp_color(COLORS["void"], COLORS["plasma"], badge_alpha * 0.3),
                               outline=lerp_color(COLORS["void"], COLORS["plasma"], badge_alpha), width=2)
        draw_centered_text(draw, "Hermes Hackathon 2026", 798, FONT_BODY, 
                          lerp_color(COLORS["void"], COLORS["white"], badge_alpha))
    
    return img


def scene_credits(progress: float) -> Image.Image:
    """
    Scene 10: Credits (78-85s)
    Quick acknowledgments.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, progress)
    
    alpha = ease_out_cubic(min(progress * 1.5, 1.0))
    
    draw_centered_text(draw, "Built with ❤️ on", 350, FONT_BODY, 
                      lerp_color(COLORS["void"], COLORS["ghost"], alpha))
    draw_centered_text(draw, "@tobi/qmd", 420, FONT_TITLE, 
                      lerp_color(COLORS["void"], COLORS["electric"], alpha))
    
    draw_centered_text(draw, "FlowState additions by Adam Manning", 550, FONT_BODY, 
                      lerp_color(COLORS["void"], COLORS["white"], alpha))
    
    draw_centered_text(draw, "Powered by Qwen3 • SQLite-vec • node-llama-cpp", 650, FONT_SMALL, 
                      lerp_color(COLORS["void"], COLORS["muted"], alpha))
    
    # Fade out
    if progress > 0.7:
        fade = (progress - 0.7) / 0.3
        overlay = Image.new("RGB", (WIDTH, HEIGHT), COLORS["void"])
        img = Image.blend(img, overlay, min(fade, 1.0))
    
    return img


# === SCENE TIMELINE - SLOWER PACING ===
SCENES = [
    ("hook", 5.0, scene_hook),              # Was 4.0
    ("problem_setup", 7.0, scene_problem_setup),   # Was 5.0
    ("problem_impact", 6.0, scene_problem_impact), # Was 4.0
    ("solution_reveal", 7.0, scene_solution_reveal),  # Was 5.0
    ("how_it_works", 11.0, scene_how_it_works),    # Was 8.0
    ("metrics", 10.0, scene_metrics),              # Was 8.0
    ("technical_proof", 10.0, scene_technical_proof), # Was 8.0
    ("demo_flow", 12.0, scene_demo_flow),          # Was 10.0
    ("tagline", 10.0, scene_tagline),              # Was 8.0
    ("credits", 7.0, scene_credits),               # Was 5.0
]

TOTAL_DURATION = sum(d for _, d, _ in SCENES)
print(f"Total video duration: {TOTAL_DURATION}s")


# === RENDERING ===

def render_all_frames():
    """Render all frames for all scenes."""
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    
    frame_index = 0
    
    for scene_name, duration, scene_fn in SCENES:
        scene_frames = int(duration * FPS)
        print(f"Rendering {scene_name} ({scene_frames} frames)...")
        
        for i in range(scene_frames):
            progress = i / max(scene_frames - 1, 1)
            frame = scene_fn(progress)
            frame_path = FRAMES_DIR / f"frame_{frame_index:05d}.png"
            frame.save(frame_path, "PNG")
            frame_index += 1
            
            if i % 30 == 0:
                print(f"  {i}/{scene_frames} frames...")
    
    print(f"Rendered {frame_index} total frames")


def encode_video():
    """Encode frames to MP4 using ffmpeg."""
    print("Encoding video...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-movflags", "+faststart",
        str(OUTPUT),
    ]
    
    subprocess.run(cmd, check=True)
    print(f"Wrote {OUTPUT}")


def cleanup():
    """Remove temporary frames."""
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
        print("Cleaned up temporary frames")


def main():
    """Main entry point."""
    print("=" * 60)
    print("FlowState-QMD Hackathon Video Generator")
    print("=" * 60)
    
    render_all_frames()
    encode_video()
    cleanup()
    
    if OUTPUT.exists():
        size_mb = OUTPUT.stat().st_size / (1024 * 1024)
        print(f"\n✓ Video ready: {OUTPUT}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"  Duration: {TOTAL_DURATION}s")
        print(f"  Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")


if __name__ == "__main__":
    main()
