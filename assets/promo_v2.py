import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import math
from concurrent.futures import ProcessPoolExecutor

# --- CONFIG ---
WIDTH, HEIGHT = 960, 540
FPS = 24
DURATION = 35  # Slightly longer to fit new content
FONT_SIZE = 12
CHAR_W, CHAR_H = 7, 12 

# --- CHAR PALETTES ---
DENSE = "@#8&o:*. "
FLOW_CHARS = "≈∞≋∽≋∿"
EVENT_CHARS = "⚡Δ∇"

def get_char(val, palette=DENSE):
    return palette[int(val * (len(palette) - 1))]

def render_frame(args):
    idx, t = args
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("Courier", FONT_SIZE)
        bold_font = ImageFont.truetype("Courier-Bold", 24)
    except:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    # --- SCENE 1: THE OLD WAY (0-5s) ---
    if t < 5:
        draw.text((WIDTH//4, HEIGHT//3), "STUCK IN POLLING HELL?", fill=(255, 50, 50), font=bold_font)
        draw.text((WIDTH//4, HEIGHT//3 + 40), "5-SECOND LAG...", fill=(200, 0, 0), font=font)
        if idx % 10 == 0:
            draw.rectangle([10, 10, WIDTH-10, HEIGHT-10], outline=(255, 0, 0), width=2)

    # --- SCENE 2: THE UPGRADE (5-15s) ---
    elif t < 15:
        # Event ripple effect
        center_x, center_y = WIDTH//2, HEIGHT//2
        radius = (t - 5) * 200 % 800
        draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], outline=(0, 255, 255), width=2)
        
        draw.text((WIDTH//2 - 150, 100), "UPGRADE: EVENT-DRIVEN WATCHER", fill=(0, 255, 255), font=bold_font)
        draw.text((WIDTH//2 - 120, 150), "FROM POLLING TO INSTANT", fill=(0, 200, 255), font=font)
        
        # Binary rain/Event rain
        for i in range(10):
            rx = (math.sin(i + t) * WIDTH) % WIDTH
            ry = (t * 300 + i * 50) % HEIGHT
            draw.text((rx, ry), "⚡ FS.WATCH", fill=(255, 255, 0), font=font)

    # --- SCENE 3: HYBRID RECALL (15-25s) ---
    elif t < 25:
        # Split screen effect
        draw.line((WIDTH//2, 0, WIDTH//2, HEIGHT), fill=(100, 100, 100), width=1)
        draw.text((100, 100), "VECTOR SEARCH", fill=(100, 255, 100), font=font)
        draw.text((WIDTH//2 + 100, 100), "FTS KEYWORDS", fill=(100, 255, 100), font=font)
        
        # Plasma background
        for y in range(150, HEIGHT-50, CHAR_H*2):
            for x in range(50, WIDTH-50, CHAR_W*4):
                val = (math.sin(x/30 + t*2) + math.cos(y/30 + t*2)) / 2
                val = (val + 1) / 2
                draw.text((x, y), "HYBRID", fill=(0, int(val*255), 150), font=font)
        
        draw.text((WIDTH//2 - 100, HEIGHT - 80), "ULTRA-LOW LATENCY RECALL", fill=(255, 255, 255), font=bold_font)

    # --- SCENE 4: OUTRO (25-35s) ---
    else:
        # Centered Logo with pulsing FLOW_CHARS
        pulse = (math.sin(t * 5) + 1) / 2
        for y in range(0, HEIGHT, CHAR_H):
            for x in range(0, WIDTH, CHAR_W):
                if 200 < x < 760 and 150 < y < 390:
                    draw.text((x, y), get_char(pulse, FLOW_CHARS), fill=(0, 100, 50), font=font)

        draw.text((WIDTH//2 - 120, HEIGHT//2 - 30), "FLOWSTATE-QMD v2.0", fill=(255, 255, 255), font=bold_font)
        draw.text((WIDTH//2 - 100, HEIGHT//2 + 20), "HE JUST KNOWS. NOW.", fill=(0, 255, 150), font=font)
        draw.text((WIDTH//2 - 130, HEIGHT - 50), "HERMES HACKATHON 2026", fill=(100, 100, 100), font=font)

    return np.array(img)

def main():
    out_dir = "frames_v2"
    os.makedirs(out_dir, exist_ok=True)
    num_frames = DURATION * FPS
    
    print(f"Rendering {num_frames} frames for v2 promo...")
    frame_indices = list(range(num_frames))
    times = [i / FPS for i in frame_indices]
    
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(render_frame, zip(frame_indices, times)))

    for i, frame in enumerate(results):
        Image.fromarray(frame).save(f"{out_dir}/frame_{i:04d}.png")

    print("Encoding v2 video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{out_dir}/frame_%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "flowstate_v2_promo.mp4"
    ]
    subprocess.run(cmd)
    print("Done! Video saved to flowstate_v2_promo.mp4")

if __name__ == "__main__":
     main()
