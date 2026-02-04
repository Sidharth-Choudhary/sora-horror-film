"""
60s horror story (Sora): 5 clips x 12s
Flow per clip: create -> poll -> download MP4 -> delete remote -> continue
Finally: concatenate with ffmpeg into out/final_60s.mp4
"""
## sora_horror_pipeline.py

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
MODEL = "sora-2"  # e.g. "sora-2"
SIZE = "1280x720"
POLL_SECONDS = 2.0

OUT_DIR = "Horror"
FINAL_OUT = os.path.join(OUT_DIR, "final_60s.mp4")

PROMPTS_DIR = "prompts"
STYLE_FILE = os.path.join(PROMPTS_DIR, "style_header.txt")


# -------------------------
# HELPERS
# -------------------------
def require_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY env var is not set. Create a .env file (see .env.example).")


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


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

    style_header = read_text(STYLE_FILE)

    clips = [
        ("clip01", 12, "clip01.txt"),
        ("clip02", 12, "clip02.txt"),
        ("clip03", 12, "clip03.txt"),
        ("clip04", 12, "clip04.txt"),
        ("clip05", 12, "clip05.txt"),
    ]

    client = OpenAI()
    mp4_paths = []

    for name, seconds, prompt_file in clips:
        print(f"\n=== Creating {name} ({seconds}s) ===")

        scene_prompt = read_text(os.path.join(PROMPTS_DIR, prompt_file))
        full_prompt = f"{style_header}\n\n{scene_prompt}\n"

        job = client.videos.create(
            model=MODEL,
            prompt=full_prompt,
            seconds=str(seconds),  # must be 4,8,12 depending on API/model
            size=SIZE,
        )

        video_id = job.id
        print(f"Video ID: {video_id} | polling...")

        done = wait_for_video(client, video_id)
        status = getattr(done, "status", None)
        print(f"Status: {status}")

        if status != "completed":
            try:
                client.videos.delete(video_id)
                print(f"Deleted remote video (failed/cancelled): {video_id}")
            except Exception as e:
                print(f"Warning: could not delete remote video {video_id}: {e}")
            raise RuntimeError(f"{name} did not complete (status={status}).")

        out_file = os.path.join(OUT_DIR, f"{name}.mp4")
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


if __name__ == "__main__":
    main()
