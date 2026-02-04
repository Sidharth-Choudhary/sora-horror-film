# 🎥 Sora Horror Short Film Generator (Python + OpenAI Video API)

This project generates a 60-second cinematic horror short film using OpenAI's Sora model.

It creates 5 clips (12s each), downloads them locally, deletes remote videos, and concatenates them into a final MP4 using FFmpeg.

## Output
- Final video: `Horror/final_60s.mp4`
- Individual clips: `Horror/clip01.mp4` ... `Horror/clip05.mp4`
- 🎬 Watch on YouTube: <https://www.youtube.com/watch?v=6ABmvijUbf0>
  
## 📖 Medium Article

I wrote a full walkthrough of this project here:

👉 **How I Built a 60-Second Horror Film Using Sora and Python**  
https://medium.com/@samaykamhai/ai-short-film-pipeline-8604d4d58676

## Tech Stack
- Python
- OpenAI API (Sora video generation)
- FFmpeg (concatenation)
- requests + python-dotenv

---

## Prerequisites

### 1) FFmpeg installed
Verify:
```bash
ffmpeg -version
```

Install:
- macOS (Homebrew): `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`
- Windows: install FFmpeg and ensure `ffmpeg` is on PATH

### 2) Python 3.9+
Verify:
```bash
python --version
```

---

## Setup

### 1) Clone repo
```bash
git clone https://github.com/Sidharth-choudhary/sora-horror-film.git
cd sora-horror-film
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Add your API key
```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=your_key_here
```

---

## Run

```bash
python sora_horror_pipeline.py
```

When it finishes, your final output is:
- `Horror/final_60s.mp4`

---

## How It Works (Pipeline)

1. Define a fixed cinematic style header for consistency  
2. Generate 5 scene-based horror clips with Sora  
3. Poll until each clip is complete  
4. Download each MP4 locally  
5. Delete remote video objects immediately  
6. Stitch all clips into one final film using FFmpeg  

---

## Notes
- The script uses **12-second clips** because the API typically supports fixed durations.
- For best continuity, keep character descriptions identical across all clip prompts.

---

## License
MIT

## Credits
Created by **Sidharth-choudhary**. Inspired by “broken toe + insomnia + fun with Sora.”
