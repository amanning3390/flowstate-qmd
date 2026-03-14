
import os
from moviepy import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx

WIDTH, HEIGHT = 1920, 1080
FPS = 24
OUTPUT_PATH = "flowstate_pitch.mp4"

COLORS = {
    'bg_dark': (10, 10, 20), 'accent_purple': (147, 51, 234),
    'accent_cyan': (34, 211, 238), 'accent_green': (34, 197, 94),
    'accent_orange': (251, 146, 60), 'text_white': (255, 255, 255),
    'text_gray': (156, 163, 175)
}

def get_font_path(bold=False):
    paths = ['/System/Library/Fonts/SF-Pro-Text-Bold.otf' if bold else '/System/Library/Fonts/SF-Pro-Text-Regular.otf',
             '/System/Library/Fonts/SFNSMono-Bold.ttf' if bold else '/System/Library/Fonts/SFNSMono.ttf']
    for p in paths:
        if os.path.exists(p): return p
    return None

def make_text(text, size, color, duration, pos='center', bold=False):
    w = int(WIDTH * 0.85)
    t = TextClip(text=text, font_size=size, color=color, font=get_font_path(bold), method='caption', size=(w, None))
    return t.with_duration(duration).with_position(pos)

# SCENES
def scene1(d=20):
    bg = ColorClip(size=(WIDTH, HEIGHT), color=COLORS['bg_dark'], duration=d)
    q = make_text('User: "What did we decide about the Q3 database migration?"', 40, COLORS['text_white'], d, ('center', 200), True)
    steps_txt = "[Thinking...]\n[Realizing missing context]\n[Formulating search query]\n[Querying RAG database]\n[Reading results]\n[Finally answering...]"
    steps = make_text(steps_txt, 36, COLORS['text_gray'], d-4, ('center', 350)).with_start(4).with_effects([vfx.FadeIn(1)])
    timer = make_text("⏱ 8.5 SECONDS WASTED", 70, COLORS['accent_orange'], d-10, ('center', 800), True).with_start(10).with_effects([vfx.FadeIn(0.5)])
    return CompositeVideoClip([bg, q, steps, timer])

def scene2(d=20):
    bg = ColorClip(size=(WIDTH, HEIGHT), color=(20, 10, 40), duration=d)
    t1 = make_text("Reactive \"Pull\" RAG", 60, COLORS['text_gray'], 6, 'center', True).with_effects([vfx.FadeOut(1)])
    t2 = make_text("Anticipatory \"Push\" Memory", 80, COLORS['accent_cyan'], d-6, 'center', True).with_start(6).with_effects([vfx.FadeIn(1)])
    tag = make_text("FlowState-QMD kills the Stutter Loop.", 40, COLORS['text_white'], d-8, ('center', 800)).with_start(8).with_effects([vfx.FadeIn(1)])
    return CompositeVideoClip([bg, t1, t2, tag])

def scene3(d=25):
    bg = ColorClip(size=(WIDTH, HEIGHT), color=COLORS['bg_dark'], duration=d)
    title = make_text("Architecture & Tech Stack", 60, COLORS['accent_purple'], d, ('center', 150), True)
    stack = make_text("Node.js  ➔  sqlite-vec  ➔  Hermes MCP", 40, COLORS['text_white'], d, ('center', 350))
    json = make_text("intuition.json directly into agent core", 36, COLORS['accent_cyan'], d-4, ('center', 450)).with_start(4).with_effects([vfx.FadeIn(1)])
    lite = make_text("Lite Mode (0.8B Models) Enabled", 50, COLORS['accent_green'], d-10, ('center', 650), True).with_start(10).with_effects([vfx.FadeIn(1)])
    ram = make_text("RAM Usage:  6GB  ➔  1.2GB", 60, COLORS['text_white'], d-14, ('center', 800), True).with_start(14).with_effects([vfx.FadeIn(1)])
    return CompositeVideoClip([bg, title, stack, json, lite, ram])

def scene4(d=20):
    bg = ColorClip(size=(WIDTH, HEIGHT), color=(10, 25, 20), duration=d)
    title = make_text("Setup in Seconds", 60, COLORS['accent_green'], d, ('center', 150), True)
    cmd = make_text("$ qmd flow start --lite", 50, COLORS['text_white'], d-2, ('center', 300)).with_start(2)
    s1 = make_text("✓ [FLOW] Monitoring Session...", 40, COLORS['text_gray'], d-4, ('center', 450)).with_start(4)
    s2 = make_text("✓ [FLOW] Intuition Cache Ready", 40, COLORS['text_gray'], d-6, ('center', 550)).with_start(6)
    race1 = make_text("Standard RAG: [Loading tool]...", 40, COLORS['accent_orange'], d-10, ('center', 750)).with_start(10)
    race2 = make_text("FlowState-QMD: [Answers Instantly - 0.1s latency]", 50, COLORS['accent_cyan'], d-12, ('center', 850), True).with_start(12).with_effects([vfx.FadeIn(0.5)])
    return CompositeVideoClip([bg, title, cmd, s1, s2, race1, race2])

def scene5(d=15):
    bg = ColorClip(size=(WIDTH, HEIGHT), color=COLORS['bg_dark'], duration=d)
    t1 = make_text("FlowState-QMD", 100, COLORS['text_white'], d, ('center', 300), True).with_effects([vfx.FadeIn(1)])
    t2 = make_text("The End of the Stutter Loop.", 50, COLORS['accent_cyan'], d-2, ('center', 500)).with_start(2).with_effects([vfx.FadeIn(1)])
    t3 = make_text("github.com/amanning3390/flowstate-qmd\nHermes 2026 Hackathon", 40, COLORS['text_gray'], d-4, ('center', 700)).with_start(4).with_effects([vfx.FadeIn(1)])
    return CompositeVideoClip([bg, t1, t2, t3])

print("Building scenes...")
final = concatenate_videoclips([scene1(), scene2(), scene3(), scene4(), scene5()], method="compose")
print("Rendering...")
final.write_videofile(OUTPUT_PATH, fps=FPS, codec='libx264', audio=False, preset='ultrafast', bitrate='4000k', threads=4, logger=None)
print("Done!")
