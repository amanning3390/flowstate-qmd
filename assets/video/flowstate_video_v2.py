#!/usr/bin/env python3
"""
FlowState QMD - Hermes Hackathon 2026 Promotional Video Generator (Optimized)
Creates a professional 1:20 video with efficient rendering.
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip, concatenate_videoclips, VideoClip
)
import time

# ============================================================
# CONFIGURATION
# ============================================================

WIDTH, HEIGHT = 1280, 720  # 720p for faster rendering
FPS = 24
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "flowstate_submission.mp4")

# Color palette
COLORS = {
    'bg_dark': (10, 10, 20),
    'bg_mid': (20, 20, 40),
    'accent_purple': (147, 51, 234),
    'accent_blue': (59, 130, 246),
    'accent_cyan': (34, 211, 238),
    'accent_green': (34, 197, 94),
    'accent_orange': (251, 146, 60),
    'text_white': (255, 255, 255),
    'text_gray': (156, 163, 175),
    'text_dim': (107, 114, 128),
    'glow_purple': (167, 139, 250),
}

# ============================================================
# FONT HELPERS
# ============================================================

_font_cache = {}

def get_font(size, bold=False):
    """Get font with caching."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    
    font_paths = [
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Menlo.ttc',
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[key] = font
                return font
            except:
                pass
    
    font = ImageFont.load_default()
    _font_cache[key] = font
    return font

# ============================================================
# FAST RENDERING
# ============================================================

def create_base_bg():
    """Create a single base background to reuse."""
    img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_dark'])
    return img

# Pre-create base background
BASE_BG = create_base_bg()

def render_scene(scene_func, duration, scene_name):
    """Render a scene efficiently using pre-rendered key frames."""
    print(f"  Rendering {scene_name} ({duration}s)...", end="", flush=True)
    start_time = time.time()
    
    # Render key frames
    num_frames = int(duration * FPS)
    
    def make_frame(t):
        frame = BASE_BG.copy()
        progress = t / duration
        return scene_func(frame, progress, t)
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(FPS)
    
    elapsed = time.time() - start_time
    print(f" done ({elapsed:.1f}s)")
    return clip

# ============================================================
# SCENE FUNCTIONS
# ============================================================

def scene_title(img, t, elapsed):
    """Title card scene."""
    draw = ImageDraw.Draw(img)
    
    # Main title
    title_font = get_font(64)
    title = "FLOWSTATE-QMD"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    x = (WIDTH - title_width) // 2
    y = HEIGHT // 3
    
    draw.text((x, y), title, font=title_font, fill=COLORS['text_white'])
    
    # Subtitle
    subtitle_font = get_font(28)
    subtitle = "Anticipatory Memory for AI Agents"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_width = bbox[2] - bbox[0]
    x = (WIDTH - sub_width) // 2
    y += 100
    draw.text((x, y), subtitle, font=subtitle_font, fill=COLORS['accent_cyan'])
    
    # Hackathon badge
    badge_font = get_font(20)
    badge = "Hermes Hackathon 2026"
    bbox = draw.textbbox((0, 0), badge, font=badge_font)
    badge_width = bbox[2] - bbox[0]
    x = (WIDTH - badge_width) // 2
    y += 60
    draw.text((x, y), badge, font=badge_font, fill=COLORS['accent_purple'])
    
    # Animated line
    line_y = y + 40
    line_width = int(300 * min(t * 2, 1))
    if line_width > 0:
        x_start = (WIDTH - 300) // 2
        draw.line([(x_start, line_y), (x_start + line_width, line_y)], 
                  fill=COLORS['accent_purple'], width=2)
    
    return np.array(img)


def scene_problem(img, t, elapsed):
    """Problem statement scene."""
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(40)
    draw.text((80, 60), "THE PROBLEM", font=title_font, fill=COLORS['accent_orange'])
    
    # Subtitle
    subtitle_font = get_font(24)
    draw.text((80, 130), "Traditional RAG forces agents into a \"Stutter Loop\":", 
              font=subtitle_font, fill=COLORS['text_gray'])
    
    # Steps
    steps = [
        "1. User asks a question",
        "2. Agent realizes it needs context",
        "3. Agent calls search tool",
        "4. Agent waits for retrieval...",
        "5. Agent finally answers",
    ]
    
    step_font = get_font(20)
    y_start = 190
    step_height = 50
    
    for i, step in enumerate(steps):
        y = y_start + i * step_height
        alpha = min(1, max(0, (t - i * 0.15) / 0.2))
        
        if alpha > 0:
            # Background bar
            bar_color = tuple(int(c * 0.2) for c in COLORS['accent_orange'])
            draw.rounded_rectangle([(100, y - 3), (100 + 500, y + 30)], 
                                   radius=6, fill=bar_color)
            
            # Step text
            text_color = tuple(int(255 * alpha) for _ in range(3))
            draw.text((120, y), step, font=step_font, fill=text_color)
    
    # Time waste indicator
    if t > 0.6:
        time_font = get_font(32)
        draw.text((700, 300), "~2-5 seconds", font=time_font, fill=COLORS['accent_orange'])
        draw.text((700, 340), "wasted per query", font=get_font(24), fill=COLORS['text_gray'])
    
    return np.array(img)


def scene_solution(img, t, elapsed):
    """Solution introduction scene."""
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(40)
    draw.text((80, 60), "THE SOLUTION", font=title_font, fill=COLORS['accent_green'])
    
    # Main concept
    concept_font = get_font(32)
    draw.text((80, 130), "What if your agent already knew?", 
              font=concept_font, fill=COLORS['text_white'])
    
    # FlowState box
    if t > 0.3:
        box_y = 220
        draw.rounded_rectangle([(80, box_y), (WIDTH - 80, box_y + 250)], 
                               radius=12, fill=(25, 25, 50), outline=COLORS['accent_purple'], width=2)
        
        # Key features
        features = [
            ("Anticipatory Retrieval", "Background engine pre-fetches context", 0.4),
            ("Intuition Cache", "Memories ready before agent starts", 0.5),
            ("Zero-Latency", "No search tool call needed", 0.6),
            ("< 50ms Read", "Instant cache access", 0.7),
        ]
        
        for i, (title, desc, appear_t) in enumerate(features):
            feat_alpha = min(1, max(0, (t - appear_t) / 0.1))
            if feat_alpha > 0:
                y = box_y + 30 + i * 55
                draw.text((120, y), "✓", font=get_font(24), fill=COLORS['accent_green'])
                draw.text((160, y), title, font=get_font(22), fill=COLORS['text_white'])
                draw.text((160, y + 25), desc, font=get_font(16), fill=COLORS['text_gray'])
    
    # Bottom tagline
    if t > 0.8:
        tagline_font = get_font(28)
        tagline = "\"Why ask when your agent already knows?\""
        bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
        tagline_width = bbox[2] - bbox[0]
        x = (WIDTH - tagline_width) // 2
        draw.text((x, HEIGHT - 100), tagline, font=tagline_font, fill=COLORS['accent_cyan'])
    
    return np.array(img)


def scene_demo(img, t, elapsed):
    """Demo scene with terminal visualization."""
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(40)
    draw.text((80, 40), "LIVE DEMO", font=title_font, fill=COLORS['accent_cyan'])
    
    # Terminal window
    term_x, term_y = 80, 120
    term_w, term_h = WIDTH - 160, HEIGHT - 200
    
    # Terminal background
    draw.rounded_rectangle([(term_x, term_y), (term_x + term_w, term_y + term_h)],
                           radius=10, fill=(15, 15, 25))
    
    # Terminal header
    draw.rectangle([(term_x, term_y), (term_x + term_w, term_y + 35)],
                   fill=(30, 30, 50))
    
    # Window buttons
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([(term_x + 12 + i * 22, term_y + 10), 
                      (term_x + 24 + i * 22, term_y + 22)], fill=color)
    
    # Terminal title
    draw.text((term_x + 80, term_y + 8), "flowstate-qmd", 
              font=get_font(14), fill=COLORS['text_gray'])
    
    # Terminal content - progressive reveal
    lines = []
    
    if t < 0.25:
        lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "→ Starting Flow Engine...",
        ]
    elif t < 0.5:
        lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "✓ Watching session log",
            "✓ Qwen3-Embedding-4B loaded",
            "⚡ Flow Engine active - monitoring...",
        ]
    elif t < 0.75:
        lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "✓ Flow Engine active",
            "",
            "$ # User asks: 'What were the Q3 results?'",
            "⚡ Intuition cache updated (2.1s)",
            "→ Top result: qmd://reports/q3-benchmarks.md (0.87)",
        ]
    else:
        lines = [
            "$ qmd flow start --watch ~/.hermes/sessions/current.log",
            "✓ Flow Engine active",
            "",
            "⚡ Intuition: 3 memories pre-fetched",
            "  1. qmd://reports/q3-benchmarks.md (0.87)",
            "  2. qmd://notes/experiment-log.md (0.72)",
            "  3. qmd://team/standup-notes.md (0.65)",
            "",
            "✓ Agent response: INSTANT (12ms cache read)",
            "⚡ \"Why ask when your agent already knows?\"",
        ]
    
    # Render terminal text
    term_font = get_font(16)
    y = term_y + 50
    line_height = 24
    
    for line in lines:
        if line.startswith('$ '):
            draw.text((term_x + 20, y), '$ ', font=term_font, fill=COLORS['accent_purple'])
            draw.text((term_x + 50, y), line[2:], font=term_font, fill=COLORS['accent_green'])
        elif line.startswith('✓ '):
            draw.text((term_x + 20, y), line, font=term_font, fill=COLORS['accent_green'])
        elif line.startswith('→ '):
            draw.text((term_x + 20, y), line, font=term_font, fill=COLORS['accent_cyan'])
        elif line.startswith('⚡ '):
            draw.text((term_x + 20, y), line, font=term_font, fill=COLORS['accent_orange'])
        else:
            draw.text((term_x + 20, y), line, font=term_font, fill=COLORS['text_gray'])
        y += line_height
    
    return np.array(img)


def scene_architecture(img, t, elapsed):
    """Architecture diagram scene."""
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(40)
    draw.text((80, 40), "ARCHITECTURE", font=title_font, fill=COLORS['accent_purple'])
    
    # Architecture boxes
    boxes = [
        ("Agent Log", 80, 180, 150, 60, COLORS['accent_orange'], 0.0),
        ("Flow Engine", 300, 180, 150, 60, COLORS['accent_purple'], 0.15),
        ("Intuition Cache", 520, 180, 150, 60, COLORS['accent_cyan'], 0.3),
        ("QMD Core", 300, 320, 150, 60, COLORS['accent_blue'], 0.25),
        ("SQLite + vec", 80, 450, 150, 60, COLORS['accent_green'], 0.4),
        ("MCP Server", 300, 450, 150, 60, COLORS['accent_green'], 0.5),
        ("CLI Tool", 520, 450, 150, 60, COLORS['accent_green'], 0.6),
        ("Hermes Agent", 740, 180, 150, 60, COLORS['accent_orange'], 0.7),
    ]
    
    # Draw boxes
    for name, x, y, w, h, color, appear_t in boxes:
        alpha = min(1, max(0, (t - appear_t) / 0.15))
        if alpha > 0:
            # Background
            bg_color = tuple(int(c * 0.3) for c in color)
            draw.rounded_rectangle([(x, y), (x + w, y + h)], 
                                   radius=8, fill=bg_color, outline=color, width=2)
            
            # Text
            text_color = tuple(int(255 * alpha) for _ in range(3))
            font = get_font(14)
            bbox = draw.textbbox((0, 0), name, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = x + (w - text_w) // 2
            text_y = y + (h - 16) // 2
            draw.text((text_x, text_y), name, font=font, fill=text_color)
    
    # Draw connections
    connections = [
        (0, 1, 0.1),  # Log → Flow Engine
        (1, 2, 0.25),  # Flow Engine → Cache
        (1, 3, 0.2),   # Flow Engine → QMD
        (3, 4, 0.35),  # QMD → SQLite
        (3, 5, 0.45),  # QMD → MCP
        (3, 6, 0.55),  # QMD → CLI
        (2, 7, 0.65),  # Cache → Hermes
    ]
    
    for from_idx, to_idx, appear_t in connections:
        alpha = min(1, max(0, (t - appear_t) / 0.1))
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
    if t > 0.8:
        label_font = get_font(14)
        draw.text((80, HEIGHT - 80), "tail -f", font=label_font, fill=COLORS['text_gray'])
        draw.text((300, HEIGHT - 80), "hybrid search", font=label_font, fill=COLORS['text_gray'])
        draw.text((520, HEIGHT - 80), "< 50ms", font=label_font, fill=COLORS['accent_green'])
    
    return np.array(img)


def scene_innovations(img, t, elapsed):
    """Key innovations scene."""
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(40)
    draw.text((80, 40), "KEY INNOVATIONS", font=title_font, fill=COLORS['accent_cyan'])
    
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
            x = 80 + col * 400
            y = 140 + row * 150
            
            # Card background
            card_color = tuple(int(c * 0.2) for c in COLORS['accent_purple'])
            draw.rounded_rectangle([(x, y), (x + 380, y + 130)], 
                                   radius=10, fill=card_color)
            
            # Number badge
            badge_font = get_font(28)
            draw.text((x + 15, y + 15), f"{i+1}", font=badge_font, fill=COLORS['accent_purple'])
            
            # Title
            title_font = get_font(22)
            draw.text((x + 55, y + 15), title, font=title_font, fill=COLORS['text_white'])
            
            # Description
            desc_font = get_font(16)
            draw.text((x + 55, y + 55), desc, font=desc_font, fill=COLORS['text_gray'])
    
    return np.array(img)


def scene_closing(img, t, elapsed):
    """Closing credits scene."""
    draw = ImageDraw.Draw(img)
    
    # Main tagline
    tagline_font = get_font(44)
    tagline = "\"Why ask when your agent already knows?\""
    bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = bbox[2] - bbox[0]
    x = (WIDTH - tagline_width) // 2
    y = HEIGHT // 4
    
    draw.text((x, y), tagline, font=tagline_font, fill=COLORS['text_white'])
    
    # Project info
    info_font = get_font(28)
    info_lines = [
        "FLOWSTATE-QMD",
        "Hermes Hackathon 2026",
        "",
        "github.com/amanning3390/flowstate-qmd",
    ]
    
    y += 100
    for line in info_lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=info_font)
            line_width = bbox[2] - bbox[0]
            x = (WIDTH - line_width) // 2
            draw.text((x, y), line, font=info_font, fill=COLORS['accent_cyan'])
        y += 45
    
    # Credits
    credit_font = get_font(20)
    credits = [
        "Built by Adam Manning",
        "",
        "Powered by QMD (by Tobi Lütke)",
        "Hermes Agent by Nous Research",
        "",
        "MIT License"
    ]
    
    y = HEIGHT - 250
    for line in credits:
        if line:
            bbox = draw.textbbox((0, 0), line, font=credit_font)
            line_width = bbox[2] - bbox[0]
            x = (WIDTH - line_width) // 2
            draw.text((x, y), line, font=credit_font, fill=COLORS['text_gray'])
        y += 30
    
    # Animated line at bottom
    line_y = HEIGHT - 40
    line_progress = min(1, t * 1.5)
    if line_progress > 0:
        line_width = int(400 * line_progress)
        x_start = (WIDTH - 400) // 2
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
    print("-" * 50)
    
    start_time = time.time()
    
    # Define scenes with timing
    scenes = [
        (scene_title, 5, "Title"),
        (scene_problem, 8, "Problem"),
        (scene_solution, 8, "Solution"),
        (scene_demo, 12, "Demo"),
        (scene_architecture, 10, "Architecture"),
        (scene_innovations, 10, "Innovations"),
        (scene_closing, 7, "Closing"),
    ]
    
    total_duration = sum(s[1] for s in scenes)
    print(f"Total duration: {total_duration}s")
    print()
    
    # Create clips for each scene
    clips = []
    for scene_fn, duration, name in scenes:
        clip = render_scene(scene_fn, duration, name)
        clips.append(clip)
    
    # Concatenate all clips
    print("\nConcatenating clips...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Write output
    print(f"Writing to {OUTPUT_PATH}...")
    final_video.write_videofile(
        OUTPUT_PATH,
        fps=FPS,
        codec='libx264',
        audio=False,
        preset='fast',
        bitrate='5000k',
        logger=None
    )
    
    elapsed = time.time() - start_time
    file_size = os.path.getsize(OUTPUT_PATH) / (1024*1024)
    
    print(f"\n{'='*50}")
    print(f"✓ Video created successfully!")
    print(f"  Path: {OUTPUT_PATH}")
    print(f"  Duration: {total_duration}s")
    print(f"  Size: {file_size:.1f} MB")
    print(f"  Render time: {elapsed:.1f}s")
    print(f"{'='*50}")
    
    return OUTPUT_PATH


if __name__ == "__main__":
    output = create_video()
