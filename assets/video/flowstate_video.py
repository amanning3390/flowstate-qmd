#!/usr/bin/env python3
"""
FlowState QMD - Hermes Hackathon 2026 Promotional Video Generator
Creates a world-class 2:30 video showcasing the anticipatory memory system.
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    TextClip, ImageClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip, VideoClip
)
import subprocess

# ============================================================
# CONFIGURATION
# ============================================================

WIDTH, HEIGHT = 1920, 1080
FPS = 30
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "flowstate_submission.mp4")

# Color palette - Deep tech aesthetic
COLORS = {
    'bg_dark': (10, 10, 20),
    'bg_mid': (20, 20, 40),
    'accent_purple': (147, 51, 234),      # Primary accent
    'accent_blue': (59, 130, 246),         # Secondary accent  
    'accent_cyan': (34, 211, 238),         # Highlight
    'accent_green': (34, 197, 94),         # Success/positive
    'accent_orange': (251, 146, 60),       # Warning/attention
    'text_white': (255, 255, 255),
    'text_gray': (156, 163, 175),
    'text_dim': (107, 114, 128),
    'glow_purple': (167, 139, 250),
}

# ============================================================
# FONT HELPERS
# ============================================================

def get_font(size, bold=False):
    """Get a clean monospace or system font."""
    font_paths = [
        '/System/Library/Fonts/SFNSMono.ttf',
        '/System/Library/Fonts/SF-Pro-Text-Regular.otf',
        '/Library/Fonts/SF-Mono-Regular.otf',
        '/System/Library/Fonts/Menlo.ttc',
        '/System/Library/Fonts/Monaco.dfont',
    ]
    bold_paths = [
        '/System/Library/Fonts/SF-Pro-Text-Bold.otf',
        '/System/Library/Fonts/SFNSMono-Bold.ttf',
    ]
    
    paths = bold_paths if bold else font_paths
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    
    # Fallback to default
    try:
        return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size)
    except:
        return ImageFont.load_default()


def get_title_font(size):
    """Get a bold display font for titles."""
    paths = [
        '/System/Library/Fonts/SF-Pro-Display-Bold.otf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return get_font(size, bold=True)


# ============================================================
# RENDERING HELPERS
# ============================================================

def create_gradient_bg(width, height, color1, color2, direction='vertical'):
    """Create a smooth gradient background."""
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            if direction == 'vertical':
                t = y / height
            elif direction == 'horizontal':
                t = x / width
            else:  # diagonal
                t = (x / width + y / height) / 2
            
            r = int(color1[0] * (1 - t) + color2[0] * t)
            g = int(color1[1] * (1 - t) + color2[1] * t)
            b = int(color1[2] * (1 - t) + color2[2] * t)
            pixels[x, y] = (r, g, b)
    
    return img


def create_grid_pattern(width, height, spacing=40, color=(30, 30, 60), opacity=0.3):
    """Create a subtle grid pattern overlay."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    alpha = int(255 * opacity)
    grid_color = (*color, alpha)
    
    for x in range(0, width, spacing):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, spacing):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    
    return img


def draw_text_with_glow(img, position, text, font, color, glow_color=None, glow_radius=3):
    """Draw text with a subtle glow effect."""
    draw = ImageDraw.Draw(img)
    x, y = position
    
    if glow_color:
        # Draw glow layers
        for offset in range(glow_radius, 0, -1):
            alpha = int(60 / offset)
            glow = (*glow_color[:3], alpha)
            for dx in range(-offset, offset + 1):
                for dy in range(-offset, offset + 1):
                    if dx*dx + dy*dy <= offset*offset:
                        draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    
    # Draw main text
    draw.text(position, text, font=font, fill=color)
    return img


def render_terminal_text(img, lines, start_y, font, text_color=(34, 197, 94), prompt_color=(147, 51, 234)):
    """Render terminal-style text with prompts."""
    draw = ImageDraw.Draw(img)
    y = start_y
    line_height = font.getbbox('Ay')[3] + 8
    
    for line in lines:
        if line.startswith('$ '):
            # Prompt line
            draw.text((100, y), '$ ', font=font, fill=prompt_color)
            draw.text((140, y), line[2:], font=font, fill=text_color)
        elif line.startswith('→ '):
            # Output line
            draw.text((100, y), line, font=font, fill=COLORS['accent_cyan'])
        elif line.startswith('✓ '):
            # Success line  
            draw.text((100, y), line, font=font, fill=COLORS['accent_green'])
        elif line.startswith('⚡ '):
            # Highlight line
            draw.text((100, y), line, font=font, fill=COLORS['accent_orange'])
        else:
            draw.text((100, y), line, font=font, fill=text_color)
        y += line_height
    
    return img


# ============================================================
# SCENE GENERATORS
# ============================================================

def make_title_frame(t):
    """Opening title card."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], COLORS['bg_mid'], 'diagonal')
    
    # Add grid overlay
    grid = create_grid_pattern(WIDTH, HEIGHT, 60, (40, 40, 80), 0.15)
    img.paste(Image.alpha_composite(Image.new('RGBA', img.size), grid).convert('RGB'))
    
    draw = ImageDraw.Draw(img)
    
    # Main title
    title_font = get_title_font(80)
    title = "FLOWSTATE-QMD"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    x = (WIDTH - title_width) // 2
    y = HEIGHT // 3
    
    # Glow effect
    draw_text_with_glow(img, (x, y), title, title_font, COLORS['text_white'], COLORS['glow_purple'], 5)
    
    # Subtitle
    subtitle_font = get_font(32)
    subtitle = "Anticipatory Memory for AI Agents"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_width = bbox[2] - bbox[0]
    x = (WIDTH - sub_width) // 2
    y += 120
    draw.text((x, y), subtitle, font=subtitle_font, fill=COLORS['accent_cyan'])
    
    # Hackathon badge
    badge_font = get_font(24)
    badge = "Hermes Hackathon 2026"
    bbox = draw.textbbox((0, 0), badge, font=badge_font)
    badge_width = bbox[2] - bbox[0]
    x = (WIDTH - badge_width) // 2
    y += 80
    draw.text((x, y), badge, font=badge_font, fill=COLORS['accent_purple'])
    
    # Animated line
    line_y = y + 60
    line_width = int(400 * min(t * 2, 1))  # Animate in
    if line_width > 0:
        x_start = (WIDTH - 400) // 2
        draw.line([(x_start, line_y), (x_start + line_width, line_y)], 
                  fill=COLORS['accent_purple'], width=2)
    
    return np.array(img)


def make_problem_frame(t):
    """The Problem: Stutter Loop visualization."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], (15, 10, 25), 'vertical')
    draw = ImageDraw.Draw(img)
    
    # Section title
    title_font = get_title_font(48)
    draw.text((100, 80), "THE PROBLEM", font=title_font, fill=COLORS['accent_orange'])
    
    # Stutter loop visualization
    subtitle_font = get_font(28)
    draw.text((100, 160), "Traditional RAG forces agents into a \"Stutter Loop\":", 
              font=subtitle_font, fill=COLORS['text_gray'])
    
    # Flow diagram
    steps = [
        ("1. User asks a question", 0.0, 0.3),
        ("2. Agent realizes it needs context", 0.3, 0.5),
        ("3. Agent calls search tool", 0.5, 0.7),
        ("4. Agent waits for retrieval...", 0.7, 0.85),
        ("5. Agent finally answers", 0.85, 1.0),
    ]
    
    step_font = get_font(24)
    y_start = 240
    step_height = 60
    
    for i, (text, start_t, end_t) in enumerate(steps):
        y = y_start + i * step_height
        alpha = min(1, max(0, (t - start_t * 0.8) / 0.2))
        
        # Background bar
        bar_color = tuple(int(c * 0.3) for c in COLORS['accent_orange'])
        if alpha > 0:
            draw.rounded_rectangle([(120, y - 5), (120 + 600, y + 35)], 
                                   radius=8, fill=bar_color)
        
        # Step text
        text_color = tuple(int(255 * alpha) for _ in range(3))
        draw.text((140, y), text, font=step_font, fill=text_color)
        
        # Arrow (except last)
        if i < len(steps) - 1 and alpha > 0.5:
            arrow_y = y + step_height - 15
            draw.text((400, arrow_y), "↓", font=step_font, fill=COLORS['accent_orange'])
    
    # Time indicator
    time_font = get_font(36)
    if t > 0.5:
        time_text = "~2-5 seconds wasted per query"
        draw.text((800, 400), time_text, font=time_font, fill=COLORS['accent_orange'])
    
    # Right side: latency visualization
    if t > 0.3:
        # Draw latency graph
        graph_x, graph_y = 900, 240
        graph_w, graph_h = 400, 300
        
        # Background
        draw.rectangle([(graph_x, graph_y), (graph_x + graph_w, graph_y + graph_h)],
                       fill=(20, 20, 40))
        
        # Axis
        draw.line([(graph_x + 50, graph_y + graph_h - 30), 
                   (graph_x + graph_w - 20, graph_y + graph_h - 30)], 
                  fill=COLORS['text_dim'], width=2)
        draw.line([(graph_x + 50, graph_y + 20), 
                   (graph_x + 50, graph_y + graph_h - 30)], 
                  fill=COLORS['text_dim'], width=2)
        
        # Bars showing time wasted
        bar_data = [0.8, 0.2, 0.9, 0.15, 0.7]  # Relative latencies
        bar_width = 50
        for i, val in enumerate(bar_data):
            bar_h = int(val * (graph_h - 80) * min(1, t * 2))
            bx = graph_x + 70 + i * 70
            by = graph_y + graph_h - 30 - bar_h
            draw.rectangle([(bx, by), (bx + bar_width, graph_y + graph_h - 30)],
                          fill=COLORS['accent_orange'])
        
        # Label
        label_font = get_font(18)
        draw.text((graph_x + 100, graph_y + graph_h - 10), "Time wasted (seconds)",
                  font=label_font, fill=COLORS['text_dim'])
    
    return np.array(img)


def make_solution_frame(t):
    """The Solution: Introducing Anticipatory Memory."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], (10, 20, 30), 'diagonal')
    draw = ImageDraw.Draw(img)
    
    # Add subtle grid
    grid = create_grid_pattern(WIDTH, HEIGHT, 80, (30, 40, 60), 0.1)
    img.paste(Image.alpha_composite(Image.new('RGBA', img.size), grid).convert('RGB'))
    draw = ImageDraw.Draw(img)
    
    # Section title
    title_font = get_title_font(48)
    draw.text((100, 80), "THE SOLUTION", font=title_font, fill=COLORS['accent_green'])
    
    # Main concept
    concept_font = get_font(36)
    draw.text((100, 160), "What if your agent already knew?", 
              font=concept_font, fill=COLORS['text_white'])
    
    # FlowState visualization
    flow_y = 260
    
    # Before/After comparison
    # Traditional (left)
    trad_x = 150
    draw.text((trad_x, flow_y), "Traditional RAG", font=get_font(24), fill=COLORS['text_gray'])
    
    trad_steps = [
        "User → Agent",
        "Agent: \"Let me search...\"",
        "Search Tool → Wait → Results",
        "Agent: \"Based on results...\"",
    ]
    
    step_font = get_font(20)
    for i, step in enumerate(trad_steps):
        alpha = min(1, max(0, (t - 0.1 * i) / 0.2))
        if alpha > 0:
            color = tuple(int(180 * alpha) for _ in range(3))
            draw.text((trad_x + 20, flow_y + 50 + i * 35), step, font=step_font, fill=color)
    
    # Arrow between
    if t > 0.4:
        draw.text((600, flow_y + 100), "→", font=get_font(60), fill=COLORS['accent_purple'])
    
    # FlowState (right)
    fs_x = 750
    if t > 0.4:
        draw.text((fs_x, flow_y), "FlowState QMD", font=get_font(24), fill=COLORS['accent_cyan'])
        
        fs_steps = [
            "Background Engine watches session",
            "Pre-fetches relevant memories",
            "Intuition Cache ready",
            "Agent: \"I already know...\"",
        ]
        
        for i, step in enumerate(fs_steps):
            step_alpha = min(1, max(0, (t - 0.5 - 0.1 * i) / 0.2))
            if step_alpha > 0:
                color = tuple(int(c * step_alpha) for c in COLORS['accent_cyan'])
                draw.text((fs_x + 20, flow_y + 50 + i * 35), step, font=step_font, fill=color)
    
    # Key insight box
    if t > 0.7:
        box_y = 520
        draw.rounded_rectangle([(100, box_y), (WIDTH - 100, box_y + 120)], 
                               radius=12, fill=(30, 30, 60), outline=COLORS['accent_purple'], width=2)
        
        insight_font = get_font(28)
        draw.text((140, box_y + 20), "Key Innovation:", font=insight_font, fill=COLORS['accent_purple'])
        draw.text((140, box_y + 60), "Anticipatory retrieval eliminates the search latency entirely.", 
                  font=get_font(22), fill=COLORS['text_white'])
    
    # Bottom: Zero latency highlight
    if t > 0.8:
        latency_font = get_font(48)
        draw.text((WIDTH // 2 - 200, HEIGHT - 120), "< 50ms Intuition", 
                  font=latency_font, fill=COLORS['accent_green'])
    
    return np.array(img)


def make_demo_frame(t):
    """Live demo section - terminal visualization."""
    img = create_gradient_bg(WIDTH, HEIGHT, (5, 5, 15), (10, 15, 25), 'vertical')
    draw = ImageDraw.Draw(img)
    
    # Section title
    title_font = get_title_font(48)
    draw.text((100, 50), "LIVE DEMO", font=title_font, fill=COLORS['accent_cyan'])
    
    # Terminal window
    term_x, term_y = 100, 150
    term_w, term_h = WIDTH - 200, HEIGHT - 250
    
    # Terminal background
    draw.rounded_rectangle([(term_x, term_y), (term_x + term_w, term_y + term_h)],
                           radius=12, fill=(15, 15, 25))
    
    # Terminal header
    draw.rectangle([(term_x, term_y), (term_x + term_w, term_y + 40)],
                   fill=(30, 30, 50))
    
    # Window buttons
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([(term_x + 15 + i * 25, term_y + 12), 
                      (term_x + 27 + i * 25, term_y + 24)], fill=color)
    
    # Terminal title
    draw.text((term_x + 100, term_y + 10), "flowstate-qmd", 
              font=get_font(16), fill=COLORS['text_gray'])
    
    # Terminal content - animated typing
    terminal_lines = []
    
    if t < 0.2:
        terminal_lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Starting Flow Engine...",
        ]
    elif t < 0.4:
        terminal_lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Starting Flow Engine...",
            "✓ Watching session log",
            "✓ Qwen3-Embedding-4B loaded",
            "⚡ Flow Engine active - monitoring...",
        ]
    elif t < 0.6:
        terminal_lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Flow Engine active",
            "",
            "$ # User asks: 'What were the Q3 results?'",
            "⚡ Intuition cache updated (2.1s)",
            "→ Top result: qmd://reports/q3-benchmarks.md (score: 0.87)",
        ]
    elif t < 0.8:
        terminal_lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Flow Engine active",
            "",
            "⚡ Intuition: 3 memories pre-fetched",
            "  1. qmd://reports/q3-benchmarks.md (0.87)",
            "  2. qmd://notes/experiment-log.md (0.72)",
            "  3. qmd://team/standup-notes.md (0.65)",
        ]
    else:
        terminal_lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Flow Engine active",
            "",
            "✓ Agent response: INSTANT",
            "  No search tool call needed!",
            "  Latency: 12ms (cache read)",
            "",
            "⚡ \"Why ask when your agent already knows?\"",
        ]
    
    # Render terminal text
    term_font = get_font(18)
    render_terminal_text(img, terminal_lines, term_y + 60, term_font)
    
    # Performance metrics on right side
    if t > 0.5:
        metrics_x = WIDTH - 400
        metrics_y = 200
        
        draw.text((metrics_x, metrics_y), "Performance", 
                  font=get_font(24), fill=COLORS['accent_purple'])
        
        metrics = [
            ("Intuition Cache Read", "< 50ms", COLORS['accent_green']),
            ("Flow Engine Cycle", "~2-3s", COLORS['accent_cyan']),
            ("BM25 Search", "< 10ms", COLORS['accent_green']),
            ("Vector Search", "< 50ms", COLORS['accent_green']),
            ("Full Hybrid + Rerank", "< 500ms", COLORS['accent_orange']),
        ]
        
        metric_font = get_font(18)
        for i, (label, value, color) in enumerate(metrics):
            my = metrics_y + 50 + i * 35
            draw.text((metrics_x, my), label, font=metric_font, fill=COLORS['text_gray'])
            draw.text((metrics_x + 200, my), value, font=metric_font, fill=color)
    
    return np.array(img)


def make_architecture_frame(t):
    """Animated architecture diagram."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], COLORS['bg_mid'], 'vertical')
    draw = ImageDraw.Draw(img)
    
    # Section title
    title_font = get_title_font(48)
    draw.text((100, 50), "ARCHITECTURE", font=title_font, fill=COLORS['accent_purple'])
    
    # Architecture boxes
    boxes = [
        # (name, x, y, w, h, color, appear_time)
        ("Agent Session Log", 100, 200, 200, 80, COLORS['accent_orange'], 0.0),
        ("Flow Engine", 400, 200, 200, 80, COLORS['accent_purple'], 0.2),
        ("Intuition Cache", 700, 200, 200, 80, COLORS['accent_cyan'], 0.4),
        ("QMD Core", 400, 400, 200, 80, COLORS['accent_blue'], 0.3),
        ("SQLite + sqlite-vec", 150, 550, 200, 80, COLORS['accent_green'], 0.5),
        ("MCP Server", 400, 550, 200, 80, COLORS['accent_green'], 0.6),
        ("CLI Tool", 650, 550, 200, 80, COLORS['accent_green'], 0.7),
        ("Hermes Agent", 1000, 200, 200, 80, COLORS['accent_orange'], 0.8),
    ]
    
    # Draw boxes
    for name, x, y, w, h, color, appear_t in boxes:
        alpha = min(1, max(0, (t - appear_t) / 0.2))
        if alpha > 0:
            # Background
            bg_color = tuple(int(c * 0.3) for c in color)
            draw.rounded_rectangle([(x, y), (x + w, y + h)], 
                                   radius=8, fill=bg_color, outline=color, width=2)
            
            # Text
            text_color = tuple(int(255 * alpha) for _ in range(3))
            font = get_font(16)
            bbox = draw.textbbox((0, 0), name, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = x + (w - text_w) // 2
            text_y = y + (h - 20) // 2
            draw.text((text_x, text_y), name, font=font, fill=text_color)
    
    # Draw connections
    connections = [
        (0, 1, 0.15),  # Log → Flow Engine
        (1, 2, 0.35),  # Flow Engine → Cache
        (1, 3, 0.25),  # Flow Engine → QMD
        (3, 4, 0.45),  # QMD → SQLite
        (3, 5, 0.55),  # QMD → MCP
        (3, 6, 0.65),  # QMD → CLI
        (2, 7, 0.75),  # Cache → Hermes
    ]
    
    for from_idx, to_idx, appear_t in connections:
        alpha = min(1, max(0, (t - appear_t) / 0.15))
        if alpha > 0:
            from_box = boxes[from_idx]
            to_box = boxes[to_idx]
            
            x1 = from_box[1] + from_box[3] // 2
            y1 = from_box[2] + from_box[4] // 2
            x2 = to_box[1] + to_box[3] // 2
            y2 = to_box[2] + to_box[4] // 2
            
            color = tuple(int(150 * alpha) for _ in range(3))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    
    # Labels
    if t > 0.9:
        label_font = get_font(18)
        draw.text((100, HEIGHT - 100), "tail -f", font=label_font, fill=COLORS['text_gray'])
        draw.text((400, HEIGHT - 100), "hybrid search", font=label_font, fill=COLORS['text_gray'])
        draw.text((700, HEIGHT - 100), "< 50ms read", font=label_font, fill=COLORS['text_gray'])
    
    return np.array(img)


def make_innovations_frame(t):
    """Key innovations showcase."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], (15, 10, 30), 'diagonal')
    draw = ImageDraw.Draw(img)
    
    # Section title
    title_font = get_title_font(48)
    draw.text((100, 50), "KEY INNOVATIONS", font=title_font, fill=COLORS['accent_cyan'])
    
    innovations = [
        ("Anticipatory Retrieval", "Pre-fetches context before it's needed", 0.0),
        ("Zero-Latency Injection", "Context in system prompt, no tool calls", 0.15),
        ("Multi-Agent Memory Pool", "One shared store for all agents", 0.3),
        ("Local-First Privacy", "All models run locally via GGUF", 0.45),
        ("GRPO Query Expansion", "Fine-tuned model for better retrieval", 0.6),
        ("Smart Chunking", "Structure-aware markdown splitting", 0.75),
    ]
    
    for i, (title, desc, appear_t) in enumerate(innovations):
        alpha = min(1, max(0, (t - appear_t) / 0.15))
        if alpha > 0:
            col = i % 3
            row = i // 3
            x = 100 + col * 600
            y = 180 + row * 200
            
            # Card background
            card_color = tuple(int(c * 0.2) for c in COLORS['accent_purple'])
            draw.rounded_rectangle([(x, y), (x + 550, y + 160)], 
                                   radius=12, fill=card_color)
            
            # Number badge
            badge_font = get_font(36)
            draw.text((x + 20, y + 20), f"{i+1}", font=badge_font, fill=COLORS['accent_purple'])
            
            # Title
            title_font = get_font(28)
            draw.text((x + 70, y + 20), title, font=title_font, fill=COLORS['text_white'])
            
            # Description
            desc_font = get_font(20)
            draw.text((x + 70, y + 70), desc, font=desc_font, fill=COLORS['text_gray'])
    
    return np.array(img)


def make_closing_frame(t):
    """Closing credits and call to action."""
    img = create_gradient_bg(WIDTH, HEIGHT, COLORS['bg_dark'], COLORS['bg_mid'], 'vertical')
    
    # Add grid
    grid = create_grid_pattern(WIDTH, HEIGHT, 60, (40, 40, 80), 0.15)
    img.paste(Image.alpha_composite(Image.new('RGBA', img.size), grid).convert('RGB'))
    draw = ImageDraw.Draw(img)
    
    # Main tagline
    tagline_font = get_title_font(56)
    tagline = "\"Why ask when your agent already knows?\""
    bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = bbox[2] - bbox[0]
    x = (WIDTH - tagline_width) // 2
    y = HEIGHT // 4
    
    draw_text_with_glow(img, (x, y), tagline, tagline_font, 
                       COLORS['text_white'], COLORS['glow_purple'], 4)
    
    # Project info
    info_font = get_font(32)
    info_lines = [
        "FLOWSTATE-QMD",
        "Hermes Hackathon 2026",
        "",
        "github.com/amanning3390/flowstate-qmd",
    ]
    
    y += 120
    for line in info_lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=info_font)
            line_width = bbox[2] - bbox[0]
            x = (WIDTH - line_width) // 2
            draw.text((x, y), line, font=info_font, fill=COLORS['accent_cyan'])
        y += 50
    
    # Credits
    credit_font = get_font(24)
    credits = [
        "Built by Adam Manning",
        "",
        "Powered by QMD (by Tobi Lütke)",
        "Hermes Agent by Nous Research",
        "",
        "MIT License"
    ]
    
    y = HEIGHT - 300
    for line in credits:
        if line:
            bbox = draw.textbbox((0, 0), line, font=credit_font)
            line_width = bbox[2] - bbox[0]
            x = (WIDTH - line_width) // 2
            draw.text((x, y), line, font=credit_font, fill=COLORS['text_gray'])
        y += 35
    
    # Animated line at bottom
    line_y = HEIGHT - 50
    line_progress = min(1, t * 1.5)
    if line_progress > 0:
        line_width = int(600 * line_progress)
        x_start = (WIDTH - 600) // 2
        draw.line([(x_start, line_y), (x_start + line_width, line_y)], 
                  fill=COLORS['accent_purple'], width=3)
    
    return np.array(img)


# ============================================================
# MAIN VIDEO ASSEMBLY
# ============================================================

def create_video():
    """Create the complete hackathon video."""
    print("Creating FlowState QMD Hackathon Video...")
    print(f"Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")
    
    # Define scenes with timing
    scenes = [
        (make_title_frame, 0, 6, "Title"),
        (make_problem_frame, 6, 14, "Problem"),
        (make_solution_frame, 14, 24, "Solution"),
        (make_demo_frame, 24, 42, "Demo"),
        (make_architecture_frame, 42, 54, "Architecture"),
        (make_innovations_frame, 54, 68, "Innovations"),
        (make_closing_frame, 68, 78, "Closing"),
    ]
    
    total_duration = scenes[-1][2]
    print(f"Total duration: {total_duration}s")
    
    # Create clips for each scene
    clips = []
    for scene_fn, start, end, name in scenes:
        duration = end - start
        print(f"  Rendering {name} ({duration}s)...")
        
        def make_frame(t, fn=scene_fn, start_t=start):
            # Normalize t to 0-1 within the scene
            return fn(t / duration)
        
        clip = VideoClip(make_frame, duration=duration)
        clip = clip.with_fps(FPS)
        clips.append(clip)
    
    # Concatenate all clips
    print("Concatenating clips...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Write output
    print(f"Writing to {OUTPUT_PATH}...")
    final_video.write_videofile(
        OUTPUT_PATH,
        fps=FPS,
        codec='libx264',
        audio=False,
        preset='medium',
        bitrate='8000k',
        logger=None
    )
    
    print(f"\n✓ Video created: {OUTPUT_PATH}")
    print(f"  Duration: {total_duration}s")
    print(f"  Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.1f} MB")
    
    return OUTPUT_PATH


if __name__ == "__main__":
    output = create_video()
    print(f"\nDone! Video saved to: {output}")
