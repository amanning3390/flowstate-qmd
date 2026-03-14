import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import math
from concurrent.futures import ProcessPoolExecutor

# --- CONFIG ---
WIDTH, HEIGHT = 1280, 720  # Higher res for judges
FPS = 24
DURATION = 45  # 45 seconds for a complete story
FONT_SIZE = 16
CHAR_W, CHAR_H = 10, 18 

# --- CHAR PALETTES ---
DENSE = "@#8&o:*. "
FLOW_CHARS = "≈∞≋∽≋∿"
BRAIN_CHARS = "🧠✨⚡"

def get_char(val, palette=DENSE):
    return palette[int(val * (len(palette) - 1))]

def draw_glitch(draw, t):
    if int(t * 10) % 7 == 0:
        for _ in range(5):
            x1, y1 = np.random.randint(0, WIDTH), np.random.randint(0, HEIGHT)
            x2, y2 = x1 + np.random.randint(50, 200), y1 + 2
            draw.rectangle([x1, y1, x2, y2], fill=(255, 0, 0))

def render_frame(args):
    idx, t = args
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("Courier", FONT_SIZE)
        bold_font = ImageFont.truetype("Courier-Bold", 32)
        heavy_font = ImageFont.truetype("Courier-Bold", 48)
    except:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        heavy_font = ImageFont.load_default()

    # --- SCENE 1: THE STUTTER (0-8s) ---
    if t < 8:
        draw.text((WIDTH//2 - 200, HEIGHT//3), "THE AGENT STUTTER", fill=(255, 50, 50), font=heavy_font)
        draw_glitch(draw, t)
        draw.text((WIDTH//2 - 250, HEIGHT//2), "Thinking... Searching... Waiting...", fill=(150, 50, 50), font=bold_font)
        draw.text((WIDTH//2 - 300, HEIGHT//2 + 60), "> [TOOL CALL] qmd_search --query 'context'...", fill=(100, 100, 100), font=font)
        if t > 5:
            draw.text((WIDTH//2 - 150, HEIGHT - 150), "FLOW: BROKEN.", fill=(255, 255, 255), font=bold_font)

    # --- SCENE 2: THE REVELATION (8-18s) ---
    elif t < 18:
        # Plasma Flow
        for y in range(0, HEIGHT, CHAR_H*2):
            for x in range(0, WIDTH, CHAR_W*4):
                val = (math.sin(x/50 + t) + math.cos(y/50 + t)) / 2
                val = (val + 1) / 2
                draw.text((x, y), get_char(val, FLOW_CHARS), fill=(0, 255, 150), font=font)
        
        draw.rectangle([WIDTH//2 - 350, HEIGHT//2 - 100, WIDTH//2 + 350, HEIGHT//2 + 100], fill=(0,0,0), outline=(255,255,255), width=3)
        draw.text((WIDTH//2 - 320, HEIGHT//2 - 60), "FLOWSTATE-QMD", fill=(255, 255, 255), font=heavy_font)
        draw.text((WIDTH//2 - 300, HEIGHT//2 + 20), "ANTICIPATORY MEMORY ENGINE", fill=(0, 255, 200), font=bold_font)

    # --- SCENE 3: THE SIXTH SENSE (18-30s) ---
    elif t < 30:
        # Scanning effect
        scan_y = int((t - 18) * 150) % HEIGHT
        draw.line((0, scan_y, WIDTH, scan_y), fill=(255, 255, 255), width=2)
        
        draw.text((100, 100), "AGENT INTUITION UNLOCKED", fill=(255, 255, 255), font=bold_font)
        draw.text((100, 160), "⚡ QWEN3-4B EMBEDDING HORIZON", fill=(0, 255, 100), font=font)
        draw.text((100, 200), "⚡ EVENT-DRIVEN FS.WATCH", fill=(0, 255, 100), font=font)
        draw.text((100, 240), "⚡ SUB-50ms ZERO-TOOL RECALL", fill=(0, 255, 100), font=font)
        
        # Draw "Sixth Sense" Brain Icon
        brain_y = HEIGHT//2
        for i in range(20):
            angle = i * (math.pi * 2 / 20) + t
            bx = WIDTH - 300 + int(80 * math.cos(angle))
            by = brain_y + int(80 * math.sin(angle))
            draw.text((bx, by), BRAIN_CHARS[i % len(BRAIN_CHARS)], fill=(255, 100, 255), font=bold_font)
        draw.text((WIDTH - 340, brain_y - 20), "SIXTH SENSE", fill=(255, 255, 255), font=bold_font)

    # --- SCENE 4: THE RESULT (30-40s) ---
    elif t < 40:
        # Two panes
        draw.line((WIDTH//2, 100, WIDTH//2, HEIGHT-100), fill=(255, 255, 255), width=2)
        draw.text((150, 150), "BEFORE: TOOL HELL", fill=(255, 100, 100), font=bold_font)
        draw.text((WIDTH//2 + 150, 150), "AFTER: PURE FLOW", fill=(100, 255, 100), font=bold_font)
        
        draw.text((150, 250), "Wait 2.5s for Search...", fill=(100, 100, 100), font=font)
        draw.text((WIDTH//2 + 150, 250), "Instant Intuition.", fill=(255, 255, 255), font=font)
        
        # Big metric
        draw.text((WIDTH//2 - 150, HEIGHT - 200), "< 50ms", fill=(255, 255, 0), font=heavy_font)
        draw.text((WIDTH//2 - 100, HEIGHT - 130), "LATENCY", fill=(255, 255, 255), font=bold_font)

    # --- SCENE 5: OUTRO (40-45s) ---
    else:
        # Pulse background
        pulse = (math.sin(t * 10) + 1) / 2
        for i in range(10):
            radius = (t - 40) * 500 + i * 50
            draw.ellipse([WIDTH//2 - radius, HEIGHT//2 - radius, WIDTH//2 + radius, HEIGHT//2 + radius], outline=(0, int(pulse*255), 100), width=1)

        draw.text((WIDTH//2 - 250, HEIGHT//2 - 40), "WIN THE HACKATHON.", fill=(255, 255, 255), font=heavy_font)
        draw.text((WIDTH//2 - 250, HEIGHT//2 + 40), "SPOOKY ACTION AT A DATA DISTANCE.", fill=(0, 255, 150), font=bold_font)
        draw.text((WIDTH//2 - 130, HEIGHT - 50), "HERMES HACKATHON 2026", fill=(100, 100, 100), font=font)

    return np.array(img)

def main():
    out_dir = "frames_v3"
    os.makedirs(out_dir, exist_ok=True)
    num_frames = DURATION * FPS
    
    print(f"Rendering {num_frames} frames for FINAL v3 JUDGE'S CUT...")
    frame_indices = list(range(num_frames))
    times = [i / FPS for i in frame_indices]
    
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(render_frame, zip(frame_indices, times)))

    for i, frame in enumerate(results):
        Image.fromarray(frame).save(f"{out_dir}/frame_{i:04d}.png")

    print("Encoding v3 video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{out_dir}/frame_%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",  # Higher quality
        "flowstate_final_submission.mp4"
    ]
    subprocess.run(cmd)
    print("Done! Video saved to flowstate_final_submission.mp4")

if __name__ == "__main__":
     main()
