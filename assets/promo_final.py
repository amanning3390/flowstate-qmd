import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import math
from concurrent.futures import ProcessPoolExecutor

# --- CONFIG ---
WIDTH, HEIGHT = 1280, 720
FPS = 24
DURATION = 60
BG_COLOR = (10, 12, 16) # Modern dark slate
TERM_BG = (20, 24, 30)
ACCENT = (0, 255, 180) # Cyan/Teal
ERROR = (255, 60, 60)
TEXT_WHITE = (240, 240, 240)
TEXT_GRAY = (150, 160, 170)

def ease_out_cubic(x):
    return 1 - pow(1 - x, 3)

def draw_terminal(draw, x, y, w, h, title, content, cursor_pos=None):
    # Window Chrome
    draw.rectangle([x, y, x+w, y+h], fill=TERM_BG, outline=(50, 60, 70), width=1)
    draw.rectangle([x, y, x+w, y+24], fill=(40, 45, 55))
    # Traffic lights
    draw.ellipse([x+8, y+8, x+16, y+16], fill=(255, 95, 86))
    draw.ellipse([x+24, y+8, x+32, y+16], fill=(255, 189, 46))
    draw.ellipse([x+40, y+8, x+48, y+16], fill=(39, 201, 63))
    # Title
    draw.text((x + w//2 - 40, y+4), title, fill=TEXT_GRAY)
    
    # Content
    lines = content.split('\n')
    line_h = 20
    start_y = y + 40
    for i, line in enumerate(lines):
        draw.text((x + 10, start_y + i*line_h), line, fill=TEXT_WHITE, font=font_mono)
        
    # Cursor
    if cursor_pos:
        cx, cy = cursor_pos
        draw.rectangle([x + 10 + cx*10, start_y + cy*line_h, x + 20 + cx*10, start_y + cy*line_h + 18], fill=ACCENT)

def render_frame(args):
    idx, t = args
    canvas = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    global font_mono, font_bold, font_header
    try:
        font_mono = ImageFont.truetype("Courier", 18)
        font_bold = ImageFont.truetype("Arial", 32)
        font_header = ImageFont.truetype("Arial Black", 64)
        font_small = ImageFont.truetype("Arial", 24)
    except:
        font_mono = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # --- PHASE 1: THE PAIN (0-10s) ---
    if t < 10:
        # Title
        op = int(255 * min(1, t))
        draw.text((80, 50), "THE PROBLEM: LATENCY", fill=(255, 255, 255), font=font_header)
        
        # Simulating laggy typing
        msg = "User: Check memory for 'Project Alpha' constraints.\nAgent: Understood. Checking..."
        progress = int((t - 1) * 10) if t > 1 else 0
        visible_msg = msg[:progress]
        
        term_text = visible_msg
        if t > 6:
            term_text += "\n> [TOOL] qmd.search('Project Alpha')..."
            # Spinner
            spin = ["|", "/", "-", "\\"][int(t*10)%4]
            term_text += f"\n  Waiting {spin}"
        
        draw_terminal(draw, WIDTH//2 - 300, HEIGHT//2 - 150, 600, 400, "Standard Agent", term_text)
        
        if t > 7:
            draw.text((WIDTH//2 - 200, HEIGHT - 100), "⚠ STUTTER DETECTED", fill=ERROR, font=font_header)

    # --- PHASE 2: THE ARCHITECTURE (10-25s) ---
    elif t < 25:
        # Fade background
        draw.text((80, 50), "THE SOLUTION: FLOWSTATE", fill=ACCENT, font=font_header)
        
        # Diagram Positions
        # Agent -> (Log) -> Engine -> (Qwen) -> Cache -> Agent
        
        # Normalize time for animation
        at = t - 10
        
        # Box 1: Agent
        draw.rectangle([100, 300, 300, 400], outline=TEXT_WHITE, width=2)
        draw.text((160, 340), "AGENT", fill=TEXT_WHITE, font=font_bold)
        
        # Arrow 1
        if at > 1:
            draw.line((300, 350, 400, 350), fill=TEXT_GRAY, width=2)
            draw.text((310, 320), "Logs", fill=TEXT_GRAY, font=font_small)

        # Box 2: Watcher (Engine)
        if at > 2:
            draw.rectangle([400, 300, 600, 400], outline=ACCENT, width=3)
            draw.text((430, 340), "FS.WATCH", fill=ACCENT, font=font_bold)
            draw.text((435, 370), "Event-Driven", fill=ACCENT, font=font_small)

        # Arrow 2
        if at > 3:
            draw.line((600, 350, 700, 350), fill=ACCENT, width=2)
            
        # Box 3: Qwen Brain
        if at > 4:
            draw.ellipse([700, 250, 900, 450], outline=(255, 0, 255), width=3)
            draw.text((740, 340), "QWEN3-4B", fill=(255, 0, 255), font=font_bold)
            
        # Arrow 3 (Loop back)
        if at > 5:
            draw.line((900, 350, 1000, 350), fill=ACCENT, width=2)
            draw.line((1000, 350, 1000, 500), fill=ACCENT, width=2)
            draw.line((1000, 500, 200, 500), fill=ACCENT, width=2)
            draw.line((200, 500, 200, 400), fill=ACCENT, width=2)
            draw.text((500, 510), "INTUITION INJECTION (< 50ms)", fill=ACCENT, font=font_bold)

    # --- PHASE 3: THE DEMO (25-45s) ---
    elif t < 45:
        at = t - 25
        
        # Split Screen Labels
        draw.text((WIDTH//4 - 100, 50), "STANDARD RAG", fill=TEXT_GRAY, font=font_bold)
        draw.text((3*WIDTH//4 - 100, 50), "FLOWSTATE-QMD", fill=ACCENT, font=font_bold)
        draw.line((WIDTH//2, 100, WIDTH//2, HEIGHT-50), fill=TEXT_GRAY)
        
        # LEFT SIDE (Standard)
        left_text = "User: Where is the config?\n"
        if at > 2: left_text += "Agent: One moment...\n"
        if at > 4: left_text += "> [TOOL] searching..."
        if at > 8: left_text += "\n> Found 3 files."
        if at > 10: left_text += "\nAgent: It is in src/config.ts"
        draw_terminal(draw, 50, 150, WIDTH//2 - 100, 400, "Old Agent", left_text)
        
        # RIGHT SIDE (Flowstate)
        right_text = "User: Where is the config?\n"
        # Instant typing
        # Simulated typing speed: very fast
        final_response = "Agent: The configuration is located\nin src/config.ts based on your\nprevious edits."
        
        char_count = int((at - 2) * 20) # 20 chars per sec start at 2s
        if char_count < 0: char_count = 0
        if char_count > len(final_response): char_count = len(final_response)
        
        right_content = right_text + final_response[:char_count]
        
        # Overlay badge
        if at > 1:
             draw.rectangle([WIDTH//2 + 350, 140, WIDTH//2 + 550, 180], fill=(0, 50, 0), outline=ACCENT)
             draw.text((WIDTH//2 + 370, 148), "INTUITION ACTIVE", fill=ACCENT, font=font_small)

        draw_terminal(draw, WIDTH//2 + 50, 150, WIDTH//2 - 100, 400, "Hermes + Flow", right_content)
        
        # Metrics
        if at > 5:
             # Left Latency
             draw.text((200, 600), "Latency: 2400ms", fill=ERROR, font=font_bold)
             # Right Latency
             draw.text((WIDTH//2 + 200, 600), "Latency: 24ms", fill=ACCENT, font=font_bold)

    # --- PHASE 4: THE SPECS (45-55s) ---
    elif t < 55:
        draw.text((80, 50), "TECHNICAL BREAKTHROUGH", fill=(255, 255, 255), font=font_header)
        
        bullets = [
            "✔ EVENT-DRIVEN FS.WATCH (No Polling)",
            "✔ QWEN3-EMBEDDING-4B (SOTA Local)",
            "✔ QWEN3-RERANKER-4B (Precision)",
            "✔ 100% LOCAL & OFFLINE",
            "✔ MULTI-AGENT IDEMPOTENCY"
        ]
        
        for i, b in enumerate(bullets):
             y_pos = 180 + i * 80
             # Fly in
             offset = (t - 45 - i*0.5)
             if offset < 0: alpha = 0
             elif offset > 1: alpha = 1
             else: alpha = ease_out_cubic(offset)
             
             x_pos = 100 + (1-alpha)*100
             if alpha > 0:
                draw.text((x_pos, y_pos), b, fill=TEXT_WHITE, font=font_bold)

    # --- PHASE 5: OUTRO (55-60s) ---
    else:
        # Drawing Logo
        cx, cy = WIDTH//2, HEIGHT//2
        draw.text((cx - 280, cy - 80), "FLOWSTATE-QMD", fill=ACCENT, font=font_header)
        draw.text((cx - 240, cy + 20), "SPOOKY ACTION AT A DATA DISTANCE", fill=TEXT_WHITE, font=font_bold)
        draw.text((cx - 150, cy + 100), "HERMES HACKATHON 2026", fill=TEXT_GRAY, font=font_small)

    return np.array(canvas)

def main():
    out_dir = "frames_final"
    os.makedirs(out_dir, exist_ok=True)
    num_frames = DURATION * FPS
    
    print(f"Rendering {num_frames} frames for CHAMPION video...")
    
    frame_indices = list(range(num_frames))
    times = [i / FPS for i in frame_indices]
    
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(render_frame, zip(frame_indices, times)))

    for i, frame in enumerate(results):
        Image.fromarray(frame).save(f"{out_dir}/frame_{i:04d}.png")

    print("Encoding final video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{out_dir}/frame_%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "slow",
        "flowstate_champion.mp4"
    ]
    subprocess.run(cmd)
    print("Done! Video saved to flowstate_champion.mp4")

if __name__ == "__main__":
     main()
