# 🎥 Sora Horror Short Film Generator (Python + OpenAI Video API)

This project generates a 60-second cinematic horror short film using OpenAI's Sora model.

It creates 5 clips (12s each), downloads them locally, deletes remote videos, and concatenates them into a final MP4 using FFmpeg.

## Final Output
🎬 Watch on YouTube: <https://www.youtube.com/watch?v=6ABmvijUbf0>

## Features
- Scene-by-scene video generation
- Character continuity prompts
- Automated polling + download
- FFmpeg stitching pipeline

## How to Run

### 1. Install dependencies
pip install -r requirements.txt

### 2. Add your API key
cp .env.example .env

### 3. Run the script
python sora_horror_pipeline.py
