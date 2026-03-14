#!/usr/bin/env python3
"""
FlowState-QMD: Final Hackathon Submission Video (Short Version)
Optimized for fast rendering while showcasing key features
"""
import os
from moviepy import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips

WIDTH, HEIGHT = 1280, 720  # Lower resolution for faster rendering
FPS = 24
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "flowstate_submission_final.mp4")

COLORS = {
    'bg_dark': (10, 10, 20),
    'accent_purple': (147, 51, 234),
    'accent_cyan': (34, 211, 238),
    'accent_green': (34, 197, 94),
    'accent_orange': (251, 146, 60),
    'text_white': (255, 255, 255),
    'text_gray': (156, 163, 175),
}

def get_font_path(bold=False):
    """Get system font path."""
    paths = [
        '/System/Library/Fonts/SF-Pro-Text-Bold.otf' if bold else '/System/Library/Fonts/SF-Pro-Text-Regular.otf',
        '/System/Library/Fonts/SFNSMono-Bold.ttf' if bold else '/System/Library/Fonts/SFNSMono.ttf',
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def make_text(text, size, color, duration, pos='center', bold=False):
    """Create text clip."""
    w = int(WIDTH * 0.85)
    t = TextClip(text=text, font_size=size, color=color, font=get_font_path(bold), 
                 method='caption', size=(w, None))
    return t.with_duration(duration).with_position(pos)

def create_bg(duration):
    """Create background clip."""
    return ColorClip(size=(WIDTH, HEIGHT), color=COLORS['bg_dark'], duration=duration)

# SCENE 1: Problem & Solution (0-30s)
def scene1():
    duration = 30
    bg = create_bg(duration)
    
    title = make_text("FLOWSTATE-QMD", 70, COLORS['accent_cyan'], duration, ('center', 100), True)
    
    problem = make_text(
        "The Stutter Loop: Traditional RAG wastes 2-5 seconds per query\n" +
        "as agents wait for search tools to retrieve context.",
        28, COLORS['text_gray'], duration, ('center', 250)
    )
    
    solution = make_text(
        "ANTICIPATORY MEMORY\n\n" +
        "FlowState pre-fetches context BEFORE the agent needs it.\n" +
        "Result: 228,702x faster (0.02ms vs 4.85s)\n\n" +
        "Zero tool calls. Agent already knows.",
        32, COLORS['accent_green'], duration, ('center', 450)
    )
    
    return CompositeVideoClip([bg, title, problem, solution])

# SCENE 2: Lite Mode & Hardware Detection (30-60s)
def scene2():
    duration = 30
    bg = create_bg(duration)
    
    title = make_text("HARDWARE AUTO-DETECTION", 60, COLORS['accent_purple'], duration, ('center', 100), True)
    
    features = make_text(
        "AUTOMATIC HARDWARE PROFILING:\n\n" +
        "1. Detects Apple Silicon (M1/M2/M3/M4)\n" +
        "2. Measures available RAM/VRAM\n" +
        "3. Recommends optimal model tier:\n" +
        "   • Standard (4B models): M2 Pro+ / 16GB+ RAM\n" +
        "   • Lite (~0.8B models): All M1/M2/M3 (8GB RAM)\n\n" +
        "CLI: qmd flow --lite ~/.hermes_history\n" +
        "MCP: fetch_anticipatory_context tool",
        28, COLORS['text_gray'], duration, ('center', 250)
    )
    
    return CompositeVideoClip([bg, title, features])

# SCENE 3: Performance & Architecture (60-90s)
def scene3():
    duration = 30
    bg = create_bg(duration)
    
    title = make_text("PERFORMANCE & ARCHITECTURE", 60, COLORS['accent_orange'], duration, ('center', 100), True)
    
    perf = make_text(
        "BENCHMARKS (Standard vs Lite):\n\n" +
        "• Intuition Cache: < 50ms (both)\n" +
        "• Model VRAM: 6.5GB vs 1.2GB\n" +
        "• Vector Search: < 50ms vs < 20ms\n" +
        "• Full Pipeline: < 500ms vs < 200ms\n\n" +
        "LOCAL-FIRST PRIVACY:\n" +
        "All models run via GGUF - zero API calls\n" +
        "MCP integration for instant context fetch\n" +
        "Smart chunking & intent-aware retrieval",
        28, COLORS['text_white'], duration, ('center', 250)
    )
    
    return CompositeVideoClip([bg, title, perf])

# SCENE 4: Call to Action (90-120s)
def scene4():
    duration = 30
    bg = create_bg(duration)
    
    title = make_text("GIVE YOUR AGENT INTUITION", 70, COLORS['accent_cyan'], duration, ('center', 150), True)
    
    cta = make_text(
        "FlowState-QMD: Anticipatory Memory for AI Agents\n\n" +
        "✓ Zero stutter loops\n" +
        "✓ Automatic hardware optimization  \n" +
        "✓ 228,702x performance improvement\n" +
        "✓ 100% local - privacy first\n" +
        "✓ Open source & production ready\n\n" +
        "github.com/amanning3390/flowstate-qmd\n" +
        "Hermes 2026 Hackathon Entry",
        32, COLORS['text_gray'], duration, ('center', 350)
    )
    
    return CompositeVideoClip([bg, title, cta])

def create_video():
    print("Creating FlowState-QMD Final Submission Video...")
    print(f"Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")
    
    print("Rendering scenes...")
    scene1_clip = scene1()
    scene2_clip = scene2()
    scene3_clip = scene3()
    scene4_clip = scene4()
    
    print("Concatenating scenes...")
    final_video = concatenate_videoclips([scene1_clip, scene2_clip, scene3_clip, scene4_clip], method="compose")
    
    print(f"Writing to {OUTPUT_PATH}...")
    final_video.write_videofile(
        OUTPUT_PATH,
        fps=FPS,
        codec='libx264',
        audio=False,
        preset='ultrafast',
        bitrate='4000k',
        threads=4,
        logger=None
    )
    
    print(f"\n✓ Video created: {OUTPUT_PATH}")
    print(f"  Duration: {final_video.duration}s")
    print(f"  Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.1f} MB")
    
    return OUTPUT_PATH

if __name__ == "__main__":
    output = create_video()
    print(f"\nDone! Final submission video saved to: {output}")