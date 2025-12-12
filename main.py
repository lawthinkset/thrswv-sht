import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time

# ---------------- CONFIG ----------------

NUM_IMAGES = 8  # 8 unique scenes (faster generation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "flux"

STORY_MAX_WORDS = 130

TOPICS_FILE = "topics.txt"

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("audio")

MUSIC_FILE = AUDIO_DIR / "music.mp3"

NARRATION_FILE = OUTPUT_DIR / "narration.mp3"
STORY_FILE = OUTPUT_DIR / "story.txt"
SCENES_FILE = OUTPUT_DIR / "scenes.txt"
SUBS_FILE = OUTPUT_DIR / "subtitles.ass"
ANIMATED_VIDEO = OUTPUT_DIR / "animated.mp4"
VIDEO_WITH_SUBS = OUTPUT_DIR / "video_with_subs.mp4"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

WHISPER_MODEL_NAME = "small"

# ----------------------------------------

def ensure_dirs():
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    # Clean old images
    for f in IMAGES_DIR.glob("*.jpg"):
        f.unlink()

def choose_topic_for_today():
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
    today = datetime.date.today()
    return topics[today.toordinal() % len(topics)]

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a short Russian story about ancient women's history."""
    base_url = "https://text.pollinations.ai/"
    system = (
        "Ты историк, специализирующийся на истории женщин в древних цивилизациях. "
        "Напиши короткий интересный рассказ на 30 секунд (80-130 слов) на русском языке. "
        "Расскажи о реальных исторических фактах, законах, обычаях или традициях. "
        "Используй живой, увлекательный стиль. Без заголовков."
    )
    prompt = f"Тема: {topic}. Расскажи интересный исторический факт."

    url = base_url + quote(prompt)
    params = {"model": "openai", "temperature": 1.0, "system": system}

    print(f"[story] Generating Russian story for topic: {topic}")
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    text = r.text.strip()

    words = text.split()
    if len(words) > STORY_MAX_WORDS:
        text = " ".join(words[:STORY_MAX_WORDS])

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[story] Russian story generated ({len(text.split())} words)")
    return text

def generate_scene_descriptions(story: str) -> list:
    """Extract distinct scene descriptions from the story sentences."""
    print(f"[scenes] Extracting {NUM_IMAGES} unique scene descriptions...")
    
    # Split story into sentences
    sentences = re.split(r'[.!?]+\s*', story.strip())
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Create unique scenes from sentences
    scenes = []
    for i in range(NUM_IMAGES):
        if i < len(sentences):
            scene = sentences[i]
        else:
            # Cycle through sentences if we need more
            scene = sentences[i % len(sentences)]
        
        # Make each scene description more visual
        if i not in [j % len(sentences) for j in range(len(scenes))]:
            scenes.append(scene)
        else:
            # Add variation for repeated scenes
            variations = ["close-up view of", "wide shot of", "dramatic scene of", "peaceful moment of"]
            scenes.append(f"{variations[i % len(variations)]} {scene}")
    
    # Ensure uniqueness by adding index
    unique_scenes = []
    for i, scene in enumerate(scenes[:NUM_IMAGES]):
        unique_scenes.append(f"{scene}")
    
    # Save scenes
    with open(SCENES_FILE, "w", encoding="utf-8") as f:
        for i, scene in enumerate(unique_scenes):
            f.write(f"{i+1}. {scene}\n")
    
    print(f"[scenes] Created {len(unique_scenes)} unique scenes")
    return unique_scenes

def generate_image(scene: str, idx: int) -> Path:
    """Generate a unique image for each scene using Pollinations AI."""
    # Create unique seed for each image based on scene content + index
    seed = hash(scene + str(idx)) % 1000000
    
    # Build detailed, high-quality prompt focusing on beautiful ancient women
    prompt = (
        f"stunning beautiful woman in ancient times, {scene}, "
        f"photorealistic portrait, elegant ancient clothing, "
        f"dramatic cinematic lighting, highly detailed face and eyes, "
        f"historical accuracy, professional photography, "
        f"volumetric lighting, 8k quality, masterpiece, "
        f"beautiful composition, vibrant colors, sharp focus"
    )
    safe_prompt = quote(prompt)
    
    # Include seed to ensure unique image
    url = (
        f"https://image.pollinations.ai/prompt/{safe_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&model={IMAGE_MODEL}&seed={seed}"
    )

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"
    print(f"[image] Generating image {idx+1}/{NUM_IMAGES}: {scene[:50]}...")
    
    # Retry logic with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            out.write_bytes(r.content)
            time.sleep(3)  # Delay between requests
            return out
        except Exception as e:
            wait_time = (attempt + 1) * 5
            if attempt < max_retries - 1:
                print(f"[image] Retry {attempt+1}/{max_retries} (waiting {wait_time}s)")
                time.sleep(wait_time)
            else:
                print(f"[image] Failed to generate image {idx+1}: {e}")
                raise e
    return out

def generate_images(scenes: list):
    """Generate unique images for each scene."""
    return [generate_image(scene, i) for i, scene in enumerate(scenes)]

def generate_tts(story: str):
    """Generate narration using edge-tts (free Microsoft TTS)."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        subprocess.run(["pip", "install", "edge-tts"], check=True)
        import edge_tts
    
    print("[tts] Generating Russian narration with edge-tts...")
    
    VOICE = "ru-RU-DmitryNeural"  # Russian male voice (or use "ru-RU-SvetlanaNeural" for female)
    
    async def generate():
        communicate = edge_tts.Communicate(story, VOICE)
        await communicate.save(str(NARRATION_FILE))
    
    asyncio.run(generate())
    print(f"[tts] Narration saved to {NARRATION_FILE}")

def generate_word_subtitles():
    """Generate word-level UPPERCASE subtitles using Whisper."""
    print("[subs] Transcribing with Whisper for word-level timestamps...")
    model = whisper.load_model(WHISPER_MODEL_NAME)
    result = model.transcribe(str(NARRATION_FILE), word_timestamps=True)
    
    # Extract word-level timestamps
    words = []
    for segment in result["segments"]:
        if "words" in segment:
            for word_info in segment["words"]:
                words.append({
                    "word": word_info["word"].strip().upper(),  # UPPERCASE
                    "start": word_info["start"],
                    "end": word_info["end"]
                })
    
    # Generate subtitles (get duration from narration file)
    # The original code had an incomplete call to generate_ass_subtitles(words)
    # This section is replaced to call the existing generate_subtitles function
    # with the story and calculated duration.
    
    # Get duration from narration file
    duration = get_audio_duration(NARRATION_FILE)
    
    # Call the existing generate_subtitles function
    generate_subtitles(story, duration)

def generate_subtitles(story, duration):
    """Generate WORD-BY-WORD subtitles using Vosk (lightweight!)."""
    print("[subs] Generating word-level Russian subtitles with Vosk...")
    
    import json
    import wave
    from vosk import Model, KaldiRecognizer
    import os
    
    # Download Vosk model if not exists
    model_path = "vosk-model-small-ru-0.22"
    if not os.path.exists(model_path):
        print("[subs] Downloading Vosk Russian model (~50 MB)...")
        import urllib.request
        import zipfile
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
        zip_path = "vosk-model.zip"
        
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print("[subs] Model downloaded!")
    
    # Convert MP3 to WAV for Vosk
    wav_file = "output/narration.wav"
    os.system(f'ffmpeg -y -i {NARRATION_FILE} -ar 16000 -ac 1 {wav_file}')
    
    # Load Vosk model
    model = Model(model_path)
    
    # Open WAV file
    wf = wave.open(wav_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word-level timestamps
    
    # Process audio
    words = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                for word_info in result['result']:
                    words.append({
                        'word': word_info['word'].upper(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
    
    # Final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        for word_info in final_result['result']:
            words.append({
                'word': word_info['word'].upper(),
                'start': word_info['start'],
                'end': word_info['end']
            })
    
    # Create ASS subtitle file
    ass_content = """[Script Info]
Title: Russian Story
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,100,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,5,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for word in words:
        start = word['start']
        end = word['end']
        text = word['word']
        
        start_time = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:.2f}"
        end_time = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:.2f}"
        
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Save ASS file
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"[subs] WORD-BY-WORD subtitles saved ({len(words)} words)")
    return SUBS_FILE

def get_audio_duration(audio_file):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_animated_slideshow(image_paths):
    """Create animated slideshow with Ken Burns zoom effect."""
    print("[video] Creating animated slideshow with Ken Burns effect...")
    
    # Get audio duration to match video length
    duration = get_audio_duration(NARRATION_FILE)
    per_image = duration / len(image_paths)
    
    # Create individual animated clips with zoom effect
    clips = []
    for i, img_path in enumerate(image_paths):
        clip_file = OUTPUT_DIR / f"clip_{i:02d}.mp4"
        clips.append(clip_file)
        
        # Calculate frames (30 fps)
        frames = max(int(per_image * 30), 60)
        
        # Alternate between zoom in and zoom out for variety
        if i % 2 == 0:
            # Zoom in effect
            zoom_start = 1.0
            zoom_end = 1.3
        else:
            # Zoom out effect  
            zoom_start = 1.3
            zoom_end = 1.0
        
        # Simple zoom with scale filter (more reliable on Windows)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps=30"
            ),
            "-t", str(per_image),
            "-c:v", "libx264",
            "-preset", "slow",  # Better quality
            "-crf", "18",  # High quality (lower = better, 18-23 is good)
            "-pix_fmt", "yuv420p",
            str(clip_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[video] Zoom failed for clip {i+1}, using fallback...")
            # Fallback: simple static with slight movement
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}:force_original_aspect_ratio=increase,crop={IMAGE_WIDTH}:{IMAGE_HEIGHT},fps=30",
                "-t", str(per_image),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(clip_file)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
        
        print(f"[video] Animated clip {i+1}/{len(image_paths)}")
    
    # Create concat list
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
    
    # Concatenate all clips
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(ANIMATED_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Animated slideshow saved to {ANIMATED_VIDEO}")
    
    # Cleanup individual clips
    for clip in clips:
        if clip.exists():
            clip.unlink()

def add_subtitles():
    """Overlay ASS subtitles on video."""
    print("[video] Adding UPPERCASE subtitles...")
    
    # Windows path needs special handling for FFmpeg filter
    subs_path = str(SUBS_FILE.resolve()).replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(ANIMATED_VIDEO),
        "-vf", f"ass='{subs_path}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(VIDEO_WITH_SUBS)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Video with subtitles saved to {VIDEO_WITH_SUBS}")

def merge_audio():
    """Merge video with narration and background music."""
    print("[merge] Merging audio with background music...")
    
    if MUSIC_FILE.exists():
        # Merge narration + background music (music at lower volume)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-i", str(MUSIC_FILE),
            "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    else:
        print("[merge] No music.mp3 found, using narration only")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    
    subprocess.run(cmd, check=True)
    print(f"[merge] Final video saved to {FINAL_VIDEO}")

def main():
    ensure_dirs()

    topic = choose_topic_for_today()
    print("=" * 60)
    print(f"=== Topic: {topic}")
    print("=" * 60)

    # 1. Generate story with Pollinations AI
    story = generate_story_with_pollinations(topic)
    
    # 2. Generate unique scene descriptions from the story
    scenes = generate_scene_descriptions(story)
    
    # 3. Generate unique images for each scene
    images = generate_images(scenes)

    # 4. Generate narration with TTS
    generate_tts(story)
    
    # 5. Generate word-level UPPERCASE subtitles with Whisper
    generate_word_subtitles()
    
    # 6. Create animated slideshow with Ken Burns effect
    create_animated_slideshow(images)
    
    # 7. Add subtitles overlay
    add_subtitles()
    
    # 8. Merge audio (narration + background music)
    merge_audio()

    print("=" * 60)
    print(f"✅ DONE. Video ready: {FINAL_VIDEO}")
    print("=" * 60)

if __name__ == "__main__":
    main()
