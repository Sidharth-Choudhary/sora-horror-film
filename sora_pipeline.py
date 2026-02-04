"""
60s horror story (Sora): 5 clips x 12s
Flow per clip: create -> poll -> download MP4 -> delete remote -> continue
Finally: concatenate with ffmpeg into out/final_60s.mp4

Requirements:
  pip install openai requests
  set OPENAI_API_KEY env var
  ffmpeg installed and on PATH (for concatenation step)
"""

import os
import time
import requests
import subprocess
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

# -------------------------
# CONFIG
# -------------------------
MODEL = "sora-2"      # or "sora-2"
SIZE = "1280x720"
POLL_SECONDS = 2.0
OUT_DIR = "Horror"
FINAL_OUT = os.path.join(OUT_DIR, "final_60s.mp4")


# -------------------------
# PROMPTS (5 x 12s = 60s)
# -------------------------

STYLE_HEADER = """
STYLE / LOOK:
- Horror short film, cinematic, realistic, moody low-key lighting
- Victorian house interior, warm lamplight vs cold hallway darkness
- Slow camera moves, subtle film grain, shallow depth of field
- Sound design notes included (optional)
- Keep characters consistent across all scenes (same wardrobe, hair, age)

CHARACTER CONTINUITY (MUST KEEP IDENTICAL IN ALL CLIPS):
1) SARAH: early 30s, tired but caring mom, pale warm skin tone, shoulder-length dark brown hair slightly messy,
   wearing a soft beige cardigan over a faded blue t-shirt, dark lounge pants.
2) LEO: 7-year-old boy, small frame, curly dark hair, wearing dinosaur-print pajamas, scared wide eyes.
3) THE OTHER MOM: looks like Sarah but uncanny—too-tall silhouette, elongated fingers, NO MOUTH (smooth skin where mouth should be),
   stands in dim hallway shadow; movement is slow, slightly jerky; never fully lit.
SETTING: Old Victorian house, creaky wood floors, narrow hallway, Leo’s bedroom upstairs, staircase, downstairs sofa.
"""

clips = [
    {
        "name": "clip01",
        "seconds": 12,
        "prompt": f"""{STYLE_HEADER}
CLIP 1 (0:00-0:12) — Bedtime dread setup
Camera: Medium close-up of Sarah tucking Leo into bed. Warm bedside lamp glow.
Leo’s eyes keep darting to the cracked door showing a thin slice of dark hallway.
Leo (whisper): "Mom? Is the Other Mom still in the hallway?"
Sarah (soft but firm): "There is no Other Mom. You're safe."
In the hallway sliver: a vague tall shadow shape, barely hinted—no clear reveal.
On-screen text (small): "11:47 PM"
Sound: faint house creaks, distant wind, subtle low drone.
"""
    },
    {
        "name": "clip02",
        "seconds": 12,
        "prompt": f"""{STYLE_HEADER}
CLIP 2 (0:12-0:24) — Sarah dismisses it, but the hallway watches
Camera: Close-up on Sarah’s face as she kisses Leo’s forehead; she looks exhausted.
Cut to POV from inside the room toward the hallway crack: darkness feels "thicker."
Leo (tiny voice): "She looks like you… but her fingers are too long. And she doesn't have a mouth."
Sarah closes the door slowly; the latch clicks loud in the quiet.
As the door shuts, we see—just for a half-second—an elongated hand shape near the frame (ambiguous).
Sound: latch click + a faint wet inhale (not a voice).
"""
    },
    {
        "name": "clip03",
        "seconds": 12,
        "prompt": f"""{STYLE_HEADER}
CLIP 3 (0:24-0:36) — 2:00 AM thump downstairs
Setting: Downstairs living room. Sarah asleep on the sofa, still in the same outfit.
On-screen text: "02:00 AM"
A muffled THUMP from upstairs. Sarah jolts awake, breath sharp.
Camera: Handheld follow as she rushes to the staircase; shadows stretch along the wall.
Upstairs: frantic footsteps across floorboards (suggest Leo running).
Sarah (urgent whisper): "Leo…?"
Sound: thump + running footsteps + creaking stairs + rising bass tension.
"""
    },
    {
        "name": "clip04",
        "seconds": 12,
        "prompt": f"""{STYLE_HEADER}
CLIP 4 (0:36-0:48) — Empty bedroom, closet sob
Camera: Sarah bursts into Leo’s room; she fumbles for the light switch—light flickers weakly.
The bed is messy; sheets tossed. Window shown clearly: LOCKED from inside.
Sarah (alarmed): "Leo! Honey, I'm here!"
She hears a tiny muffled sob from the walk-in closet.
Camera: Tight shot on Sarah’s hand grabbing the closet handle—her fingers tremble.
Sound: light buzz + Leo’s sob + distant house groan.
"""
    },
    {
        "name": "clip05",
        "seconds": 12,
        "prompt": f"""{STYLE_HEADER}
CLIP 5 (0:48-1:00) — Twist + the Other Mom approaches
Camera: Closet open. Leo is curled behind coats, shaking. Same pajamas, tear-streaked face.
Sarah kneels, reaching for him.
Leo shrinks back, staring past Sarah to the open doorway.
Leo (whisper-sob): "Mom… if you’re in here… then who just tucked me back in?"
Sarah freezes. Over her shoulder: hallway darkness.
From the hallway: slow WET dragging sound against carpet.
A voice identical to Sarah but hollow (from darkness): "Go back to sleep, Leo… Mommy’s coming back for the rest of you."
In the hallway shadow: The Other Mom’s silhouette edges into frame—elongated fingers visible; face smooth where mouth should be.
End on BLACK with bold text: "THE OTHER MOM"
Sound: dragging + whisper + sudden silence cutoff.
"""
    }
]

# -------------------------
# HELPERS
# -------------------------
def require_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY env var is not set.")

def wait_for_video(client: OpenAI, video_id: str, poll_s: float = POLL_SECONDS):
    while True:
        v = client.videos.retrieve(video_id)
        status = getattr(v, "status", None)
        if status in ("completed", "failed", "cancelled"):
            return v
        time.sleep(poll_s)

def download_video_via_http(video_id: str, out_path: str):
    """
    Download using the raw REST endpoint:
      GET https://api.openai.com/v1/videos/{video_id}/content

    This avoids SDK helper-method differences (like missing .content()).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    url = f"https://api.openai.com/v1/videos/{video_id}/content"
    headers = {"Authorization": f"Bearer {api_key}"}

    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def concat_with_ffmpeg(mp4_paths, final_out_path):
    """
    Concatenate mp4 files with ffmpeg concat demuxer.
    """
    list_file = os.path.join(OUT_DIR, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in mp4_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", final_out_path],
        check=True
    )

# -------------------------
# MAIN
# -------------------------
def main():
    require_api_key()
    os.makedirs(OUT_DIR, exist_ok=True)

    client = OpenAI()
    mp4_paths = []

    for c in clips:
        print(f"\n=== Creating {c['name']} ({c['seconds']}s) ===")

        job = client.videos.create(
            model=MODEL,
            prompt=c["prompt"],
            seconds=str(c["seconds"]),  # must be 4,8,12
            size=SIZE,
        )

        video_id = job.id
        print(f"Video ID: {video_id} | polling...")

        done = wait_for_video(client, video_id)
        status = getattr(done, "status", None)
        print(f"Status: {status}")

        if status != "completed":
            # Clean up remote object even if failed
            try:
                client.videos.delete(video_id)
                print(f"Deleted remote video (failed/cancelled): {video_id}")
            except Exception as e:
                print(f"Warning: could not delete remote video {video_id}: {e}")
            raise RuntimeError(f"{c['name']} did not complete (status={status}).")

        out_file = os.path.join(OUT_DIR, f"{c['name']}.mp4")
        print(f"Downloading to {out_file} ...")
        download_video_via_http(video_id, out_file)
        mp4_paths.append(out_file)
        print("Download complete.")

        # Delete from OpenAI storage immediately after download
        print(f"Deleting remote video {video_id} ...")
        client.videos.delete(video_id)
        print("Remote delete complete.")    
    
    print("\n=== Concatenating clips into final video ===")
    concat_with_ffmpeg(mp4_paths, FINAL_OUT)
    print(f"Done: {FINAL_OUT}")

if __name__ == "__main__":
    main()
