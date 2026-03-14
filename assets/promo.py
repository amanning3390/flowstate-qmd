import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import math
from concurrent.futures import ProcessPoolExecutor

# --- CONFIG ---
WIDTH, HEIGHT = 960, 540
FPS = 24
DURATION = 30  # 30 seconds of pure flow
FONT_SIZE = 12
CHAR_W, CHAR_H = 7, 12  # Approximation

# --- CHAR PALETTES ---
DENSE = "@#8&o:*. "
MATRIX = "01 "
FLOW_CHARS = "≈∞≋∽≋∿"

def get_char(val, palette=DENSE):
    return palette[int(val * (len(palette) - 1))]

def render_frame(args):
    idx, t = args
    # Create canvas
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    
    # Load font (falling back to default)
    try:
        font = ImageFont.truetype("Courier", FONT_SIZE)
    except:
        font = ImageFont.load_default()

    # --- SCENE LOGIC ---
    if t < 5:  # INTRO: STUTTER
        draw.text((WIDTH//4, HEIGHT//3), "STUCK IN SEARCH HELL?", fill=(255, 50, 50), font=font)
        # Add "stutter" glitches
        if idx % 5 == 0:
            draw.rectangle([0, 0, WIDTH, HEIGHT], outline=(255, 0, 0), width=5)
            draw.text((WIDTH//2, HEIGHT//2), "WAIIIIIIITING...", fill=(255, 0, 0), font=font)
            
    elif t < 15: # THE REVELATION
        # Plasma background
        for y in range(0, HEIGHT, CHAR_H):
            for x in range(0, WIDTH, CHAR_W):
                val = (math.sin(x/50 + t) + math.sin(y/50 + t) + math.sin((x+y)/50 + t)) / 3
                val = (val + 1) / 2
                char = get_char(val, FLOW_CHARS)
                draw.text((x, y), char, fill=(0, 255, 100), font=font)
        
        # Centered Logo
        logo_text = "FLOWSTATE-QMD"
        draw.text((WIDTH//2 - 100, HEIGHT//2 - 20), logo_text, fill=(255, 255, 255), font=font)
        draw.text((WIDTH//2 - 80, HEIGHT//2 + 10), "HE JUST KNOWS.", fill=(200, 200, 255), font=font)

    elif t < 25: # FEATURE BULLETS
        draw.text((50, 50), "• QWEN3-4B EMBEDDINGS", fill=(0, 255, 200), font=font)
        draw.text((50, 80), "• QWEN3-4B RERANKER", fill=(0, 255, 200), font=font)
        draw.text((50, 110), "• ZERO-TOOL INTUITION", fill=(0, 255, 200), font=font)
        draw.text((50, 140), "• SUB-50MS LATENCY", fill=(0, 255, 200), font=font)
        
        # Animate a "Flow" wave at the bottom
        for x in range(0, WIDTH, 10):
            y_wave = HEIGHT - 100 + int(20 * math.sin(x/40 + t*3))
            draw.text((x, y_wave), "≋", fill=(100, 100, 255), font=font)

    else: # OUTRO
        draw.text((WIDTH//3, HEIGHT//2), "WIN THE HACKATHON.", fill=(255, 255, 255), font=font)
        draw.text((WIDTH//3, HEIGHT//2 + 30), "HERMES HACKATHON 2026", fill=(150, 150, 150), font=font)

    return np.array(img)

def main():
    out_dir = "frames"
    os.makedirs(out_dir, exist_ok=True)
    num_frames = DURATION * FPS
    
    print(f"Rendering {num_frames} frames...")
    
    # Process frames in parallel
    frame_indices = list(range(num_frames))
    times = [i / FPS for i in frame_indices]
    
    # Using a subset for faster demo if needed, but here we go full
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(render_frame, zip(frame_indices, times)))

    # Save frames and encode
    for i, frame in enumerate(results):
        Image.fromarray(frame).save(f"{out_dir}/frame_{i:04d}.png")

    print("Encoding video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{out_dir}/frame_%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "flowstate_promo.mp4"
    ]
    subprocess.run(cmd)
    print("Done! Video saved to flowstate_promo.mp4")

if __name__ == "__main__":
     main()
