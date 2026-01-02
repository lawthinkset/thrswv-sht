import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- CONFIG ----------------

# Pollinations AI API Configuration (PAID)
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
TEXT_MODEL = "mistral"  # Works great with Russian text
IMAGE_MODEL = "turbo"  # Affordable and fast (using negative prompts to prevent deformations)

NUM_IMAGES = 12  # 12 unique scenes for better visual variety
IMAGE_WIDTH = 720   # Initial generation at 720x1280 (safer for Turbo model)
IMAGE_HEIGHT = 1280 # Will be upscaled to 1080x1920 for HD YouTube
FINAL_WIDTH = 1080  # Final upscaled width for HD YouTube
FINAL_HEIGHT = 1920 # Final upscaled height for HD YouTube

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
    """Reads the FIRST topic, removes it from file, and returns it (Queue system)."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
    
    if not topics:
        raise ValueError("No topics found in topics.txt! Please run generate_topics.py")
        
    # Pick the first one (Queue: FIFO)
    today_topic = topics[0]
    
    # Write back the rest (effectively deleting the first one)
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        for t in topics[1:]:
            f.write(t + "\n")
            
    return today_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a short Russian story about ancient women's history using PAID API."""
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY not set! Get your API key from https://enter.pollinations.ai")
    
    # Use OpenAI-compatible endpoint for paid API
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты историк, специализирующийся на истории женщин в древних цивилизациях. "
        "Напиши короткий интересный рассказ на 30 секунд (80-130 слов) на русском языке. "
        "Расскажи о реальных исторических фактах, законах, обычаях или традициях. "
        "Используй живой, увлекательный стиль. Без заголовков."
    )
    
    user_prompt = f"Тема: {topic}. Расскажи интересный исторический факт."
    
    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1.0,
        "max_tokens": 500
    }

    print(f"[story] Generating Russian story for topic: {topic}")
    print(f"[story] Using model: {TEXT_MODEL} (PAID API)")
    
    # Retry logic - paid API should be more reliable
    max_retries = 3
    retry_delays = [30, 60, 120]  # 30s, 1min, 2min (much faster than free API)
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            print(f"[story] Attempt {attempt+1}/{max_retries}...")
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            
            response_data = r.json()
            
            # Extract text from OpenAI-compatible response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                text = response_data["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("Invalid response format from API")
            
            # Validate response
            if not text or len(text) < 50:
                raise ValueError("Story too short or empty")
            
            words = text.split()
            if len(words) > STORY_MAX_WORDS:
                text = " ".join(words[:STORY_MAX_WORDS])

            with open(STORY_FILE, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[story] ✅ Russian story generated ({len(text.split())} words)")
            
            # Show usage info if available
            if "usage" in response_data:
                usage = response_data["usage"]
                print(f"[story] 📊 Tokens used: {usage.get('total_tokens', 'N/A')}")
            
            return text
            
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[story] ⏱️ Timeout! Retry {attempt+2}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[story] ❌ Failed after {max_retries} attempts (timeout)")
                
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else "Unknown"
            error_body = e.response.text if e.response else "No response body"
            
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[story] ❌ HTTP {status_code} Error! Retry {attempt+2}/{max_retries} in {wait_time}s...")
                print(f"[story] Error details: {error_body[:200]}")
                time.sleep(wait_time)
            else:
                print(f"[story] ❌ Failed after {max_retries} attempts: HTTP {status_code}")
                print(f"[story] Error: {error_body}")
                
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[story] ❌ Error: {e}. Retry {attempt+2}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[story] ❌ Failed after {max_retries} attempts: {e}")
    
    # If we get here, all retries failed
    error_msg = f"Story generation failed after {max_retries} attempts. Last error: {last_error}"
    print(f"[story] {error_msg}")
    raise Exception(error_msg)

def generate_scene_descriptions(story: str) -> list:
    """Generate detailed visual scene prompts from the story using AI."""
    print(f"[scenes] Generating {NUM_IMAGES} detailed scene prompts with AI...")
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY not set!")
    
    # Use AI to extract and enhance scene descriptions
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        f"You are a world-renowned fashion photographer and beauty director creating a photoshoot of the most EXCEPTIONALLY BEAUTIFUL ancient goddesses. "
        f"Read the following story and create exactly {NUM_IMAGES} stunning portrait descriptions. "
        f"Each description MUST capture the MOST BEAUTIFUL, CAPTIVATING, FLAWLESS ancient woman imaginable. "
        f"\n\nFOCUS ON EXCEPTIONAL BEAUTY:\n"
        f"- PERFECT FACIAL FEATURES: Stunning sharp jawline, high cheekbones, symmetrical face, flawless skin\n"
        f"- EXCEPTIONAL HAIR: Luxurious voluminous hair, perfectly styled, elaborate braids, glossy and thick\n"
        f"- CAPTIVATING EYES: Large expressive eyes, intense mesmerizing gaze, perfectly shaped eyebrows\n"
        f"- BEAUTIFUL LIPS: Full sensual lips, perfect shape, natural rosy color\n"
        f"- RADIANT SKIN: Glowing porcelain complexion, luminous dewy skin, golden hour glow\n"
        f"- GODDESS-LIKE PRESENCE: Regal posture, confident expression, alluring mysterious aura\n"
        f"\n\nVISUAL ELEMENTS:\n"
        f"- ELABORATE GOLD JEWELRY: Massive necklaces, ornate earrings, jeweled headpieces, arm bands\n"
        f"- LUXURIOUS ANCIENT ATTIRE: Elegant robes with tasteful necklines, golden embroidery, rich fabrics\n"
        f"- DRAMATIC LIGHTING: Golden sunlight, warm amber tones, chiaroscuro, rim lighting\n"
        f"- ANCIENT ATMOSPHERE: Palace backgrounds, marble columns, golden ambiance, ethereal setting\n"
        f"\n\nEXAMPLES OF PERFECT DESCRIPTIONS:\n"
        f"'Breathtaking goddess with piercing emerald eyes and stunning sharp jawline, luxurious cascading hair adorned with gold, massive ornate necklace, golden palace sunlight'\n"
        f"'Exceptionally beautiful woman with perfect symmetrical face, voluminous glossy braided hair with jewels, alluring mysterious smile, elaborate gold jewelry, dramatic lighting'\n"
        f"'Mesmerizing ancient beauty with flawless porcelain skin, thick flowing silky hair, captivating intense gaze, ornate gold headpiece, regal powerful presence'\n"
        f"\n\nReturn ONLY the portrait descriptions, numbered 1 to {NUM_IMAGES}, one per line. "
        f"Make each portrait VISUALLY STUNNING, EXCEPTIONALLY BEAUTIFUL, and UNFORGETTABLE."
    )
    
    user_prompt = f"Story:\n{story}\n\nGenerate {NUM_IMAGES} detailed visual scene descriptions:"
    
    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1000
    }
    
    max_retries = 3
    retry_delays = [30, 60, 120]
    
    for attempt in range(max_retries):
        try:
            print(f"[scenes] Attempt {attempt+1}/{max_retries}...")
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            
            response_data = r.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                text = response_data["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError("Invalid response format from API")
            
            # Parse scene descriptions
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            scenes = []
            
            for line in lines:
                # Remove numbering (1., 2., etc.)
                scene = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if scene and len(scene) > 20:  # Valid scene description
                    scenes.append(scene)
            
            # Ensure we have exactly NUM_IMAGES scenes
            if len(scenes) < NUM_IMAGES:
                # Duplicate some scenes with variations if needed
                while len(scenes) < NUM_IMAGES:
                    idx = len(scenes) % len(scenes) if scenes else 0
                    variations = ["close-up of", "wide angle of", "dramatic view of", "atmospheric scene of"]
                    scenes.append(f"{variations[idx % len(variations)]} {scenes[idx] if scenes else 'ancient woman'}")
            
            scenes = scenes[:NUM_IMAGES]
            
            # Save scenes
            with open(SCENES_FILE, "w", encoding="utf-8") as f:
                for i, scene in enumerate(scenes):
                    f.write(f"{i+1}. {scene}\n")
            
            print(f"[scenes] ✅ Generated {len(scenes)} detailed scene prompts")
            for i, scene in enumerate(scenes[:3]):  # Show first 3
                print(f"[scenes]   {i+1}. {scene[:80]}...")
            
            return scenes
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[scenes] ❌ Error: {e}. Retry {attempt+2}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[scenes] ❌ Failed to generate scenes with AI, falling back to simple extraction")
                # Fallback to simple sentence extraction
                sentences = re.split(r'[.!?]+\s*', story.strip())
                sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
                
                scenes = []
                for i in range(NUM_IMAGES):
                    if i < len(sentences):
                        scenes.append(sentences[i])
                    else:
                        scenes.append(sentences[i % len(sentences)])
                
                return scenes[:NUM_IMAGES]
    
    return scenes

def translate_to_english(russian_text: str) -> str:
    """Translate Russian text to English using Pollinations AI PAID API."""
    
    if not POLLINATIONS_API_KEY:
        print("[translate] Warning: No API key, using original text")
        return russian_text
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "user", "content": f"Translate this Russian text to English (only output the translation, nothing else): {russian_text}"}
        ],
        "temperature": 0.3,
        "max_tokens": 300
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        
        response_data = r.json()
        if "choices" in response_data and len(response_data["choices"]) > 0:
            translation = response_data["choices"][0]["message"]["content"].strip()
            # Remove any quotes or extra text
            translation = translation.strip('"').strip("'").strip()
            return translation
        else:
            raise ValueError("Invalid response format")
            
    except Exception as e:
        print(f"[translate] Warning: Translation failed ({e}), using original text")
        return russian_text

def generate_image(scene: str, idx: int) -> Path:
    """Generate a unique image for each scene using Pollinations AI PAID API with robust retry logic."""
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY not set! Get your API key from https://enter.pollinations.ai")
    
    # Translate Russian scene to English for better API stability
    scene_english = translate_to_english(scene)
    print(f"[image] Translated scene: {scene_english[:80]}...")
    
    # Create unique seed for each image based on scene content + index
    seed = hash(scene + str(idx)) % 1000000
    
    # MAXIMUM BEAUTY + ANCIENT GODDESS AESTHETIC + YOUTUBE-SAFE (cleavage OK, nipples NOT OK)
    # Focus: EXCEPTIONAL BEAUTY, PERFECT HAIR, STUNNING JAWLINE, CAPTIVATING EYES
    # Safety: Cleavage allowed, but NO NIPPLES (YouTube-safe)
    # Quality: FLAWLESS FACE, PERFECT HAIR, BEAUTIFUL FEATURES
    prompt = (
        f"breathtaking portrait of the most exceptionally beautiful ancient goddess, {scene_english}, "
        f"EXTREME CLOSE-UP portrait, face and upper body, mesmerizing ethereal beauty, "
        
        # PERFECT FACIAL FEATURES
        f"ABSOLUTELY FLAWLESS FACE, perfect symmetrical features, divine goddess-like appearance, "
        f"STUNNING SHARP JAWLINE, sculpted defined jaw, elegant graceful jawline, "
        f"high prominent cheekbones, refined facial structure, aristocratic features, "
        
        # CAPTIVATING EYES
        f"CRYSTAL CLEAR piercing eyes, large expressive eyes, intense mesmerizing gaze, "
        f"soul-piercing captivating stare, hypnotic eye contact, alluring mysterious eyes, "
        f"perfectly shaped eyebrows, long elegant lashes, "
        
        # BEAUTIFUL LIPS & SKIN
        f"full sensual lips, perfect lip shape, natural rosy lips, "
        f"RADIANT GLOWING SKIN, porcelain smooth complexion, luminous dewy skin, "
        f"golden hour glow on face, flawless skin texture, "
        
        # EXCEPTIONAL HAIR (CRITICAL FOR BEAUTY)
        f"LUXURIOUS VOLUMINOUS HAIR, thick flowing silky hair, "
        f"PERFECTLY STYLED ANCIENT HAIR, elaborate intricate braids, "
        f"cascading waves, glossy shimmering hair, "
        f"ornate gold hair accessories, jeweled headpiece, golden hair ornaments, "
        f"hair adorned with precious gems, elaborate hair styling, "
        
        # ELEGANT NECK & POSTURE
        f"long graceful neck, elegant swan-like neck, regal posture, "
        f"confident powerful stance, goddess-like presence, "
        
        # GOLD JEWELRY & ANCIENT ATTIRE
        f"COVERED IN ELABORATE GOLD JEWELRY, massive ornate gold necklaces, "
        f"intricate gold earrings, ancient gold arm bands, shimmering gold bracelets, "
        f"wearing elegant ancient robes with DEEP V-NECKLINE showing tasteful cleavage, "
        f"golden embroidered dress, rich luxurious fabric with gold thread, "
        f"draped silk garments, regal ancient royal attire, "
        
        # LIGHTING & ATMOSPHERE
        f"dramatic cinematic lighting, golden sunlight, warm amber tones, "
        f"chiaroscuro lighting, rim lighting, soft glow, "
        f"ancient palace background, marble columns, golden atmosphere, "
        f"shimmering light, ethereal ambiance, "
        
        # PHOTOGRAPHY QUALITY
        f"shot on Hasselblad medium format, 85mm portrait lens, f/1.4 shallow depth of field, "
        f"professional fashion photography, Vogue magazine quality, editorial style, "
        f"high fashion beauty shoot, award-winning portrait, "
        
        # EXPRESSION & MOOD
        f"regal powerful expression, confident seductive look, "
        f"mysterious alluring aura, captivating presence, "
        f"ancient Egyptian/Greek/Roman aesthetic, timeless beauty, divine presence, "
        
        # TECHNICAL QUALITY
        f"8k ultra high definition, razor sharp focus on eyes, "
        f"hyperrealistic, photorealistic, masterpiece, award winning, "
        f"perfect composition, professional color grading"
    )
    
    # STRICT NIPPLE PREVENTION + ANTI-DEFORMITY (cleavage is OK, nipples are NOT)
    negative_prompt = (
        # CRITICAL: Prevent nipples (YouTube ban) but allow cleavage
        "nipples, areola, exposed nipples, visible nipples, bare nipples, erect nipples, "
        "topless, nude breasts, naked breasts, exposed breasts, bare breasts, "
        "nsfw, explicit, pornographic, sexual content, adult content, "
        
        # Prevent excessive exposure (keep it classy)
        "completely naked, fully nude, no clothing, transparent clothing, see-through, "
        
        # CRITICAL: Prevent HAIR deformities (HAIR IS CRITICAL FOR BEAUTY)
        "bad hair, messy hair, tangled hair, frizzy hair, damaged hair, "
        "thin hair, balding, bald spots, receding hairline, "
        "unnatural hair, fake hair, wig-like hair, plastic hair, "
        "hair covering face, hair in eyes, hair obscuring features, "
        "poorly drawn hair, deformed hair, missing hair, "
        
        # CRITICAL: Prevent FACIAL deformities (quality control)
        "blurry eyes, crossed eyes, asymmetric eyes, closed eyes, lazy eye, wall-eyed, "
        "different sized eyes, uneven eyes, misaligned eyes, "
        "deformed face, disfigured face, ugly face, distorted face, malformed face, "
        "asymmetric face, crooked face, lopsided face, uneven features, "
        "bad jawline, weak chin, double chin, undefined jawline, "
        "bad teeth, crooked teeth, missing teeth, ugly smile, "
        "bad nose, crooked nose, large nose, deformed nose, "
        
        # Prevent body deformities
        "bad anatomy, wrong anatomy, extra limbs, missing limbs, fused fingers, "
        "extra fingers, mutated hands, poorly drawn hands, deformed hands, "
        "mutation, deformed, bad proportions, gross proportions, "
        "long neck, giraffe neck, stretched neck, elongated neck, thin neck, "
        "two heads, multiple heads, double face, duplicate face, conjoined, "
        "multiple people, crowd, group, two women, three women, "
        
        # Prevent bad styles (maintain realism)
        "cartoon, anime, manga, illustration, drawing, painting, sketch, "
        "3d render, cgi, digital art, artificial, synthetic, computer generated, "
        "plastic skin, doll face, mannequin, wax figure, fake, "
        "overly smooth skin, airbrushed, heavily photoshopped, filtered, "
        
        # Prevent bad composition
        "full body, wide shot, distant, far away, tiny face, small face, "
        "cropped face, cut off head, partial face, incomplete face, "
        "back view, rear view, side profile only, looking away, "
        "looking down, looking up, eyes closed, "
        
        # Prevent low quality
        "low quality, low resolution, pixelated, grainy, noisy, blurry, blurry face, "
        "watermark, text, logo, signature, username, caption, "
        "jpeg artifacts, compression artifacts, distorted, "
        "out of focus, soft focus, motion blur, "
        "amateur, unprofessional, poor lighting, bad lighting"
    )
    
    safe_prompt = quote(prompt)
    safe_negative = quote(negative_prompt)
    
    # Use paid API endpoint with authentication
    model_param = f"&model={IMAGE_MODEL}" if IMAGE_MODEL else ""
    url = (
        f"https://gen.pollinations.ai/image/{safe_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}{model_param}&seed={seed}"
        f"&nologo=true&nofeed=true&negative={safe_negative}"
    )
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"
    print(f"[image] Generating image {idx+1}/{NUM_IMAGES} with {IMAGE_MODEL} (PAID API): {scene[:50]}...")
    
    # Enhanced retry logic - paid API should be faster and more reliable
    max_retries = 5
    retry_delays = [10, 20, 30, 60, 120]  # 10s, 20s, 30s, 1min, 2min (faster than free)
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=120)
            r.raise_for_status()
            
            # Validate image data
            if len(r.content) < 1000:  # Too small to be a valid image
                raise ValueError("Image data too small, likely failed generation")
            
            out.write_bytes(r.content)
            print(f"[image] ✅ Image {idx+1} generated successfully ({len(r.content)//1024}KB)")
            time.sleep(2)  # Small delay between successful requests
            return out
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[image] ⏱️ Timeout! Retry {attempt+2}/{max_retries} (waiting {wait_time}s)...")
                time.sleep(wait_time)
            else:
                print(f"[image] ❌ Failed to generate image {idx+1}: Timeout after {max_retries} attempts")
                raise
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            error_body = e.response.text if e.response else "No response"
            
            # Handle 429 rate limits (shouldn't happen with paid API but just in case)
            if status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delays[attempt] * 2  # Double wait time for rate limits
                    print(f"[image] 🚫 Rate limited! Retry {attempt+2}/{max_retries} (waiting {wait_time}s)...")
                    time.sleep(wait_time)
                else:
                    print(f"[image] ❌ Failed to generate image {idx+1}: Rate limit exceeded")
                    raise
            else:
                if attempt < max_retries - 1:
                    wait_time = retry_delays[attempt]
                    print(f"[image] ❌ HTTP {status_code}! Retry {attempt+2}/{max_retries} (waiting {wait_time}s)...")
                    print(f"[image] Error: {error_body[:200]}")
                    time.sleep(wait_time)
                else:
                    print(f"[image] ❌ Failed to generate image {idx+1}: HTTP {status_code}")
                    print(f"[image] Error: {error_body}")
                    raise
                    
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"[image] ❌ Error: {e}. Retry {attempt+2}/{max_retries} (waiting {wait_time}s)...")
                time.sleep(wait_time)
            else:
                print(f"[image] ❌ Failed to generate image {idx+1} after {max_retries} attempts: {e}")
                raise
    
    raise Exception(f"Image {idx+1} generation failed after all retries")

def upscale_image(image_path: Path) -> Path:
    """Upscale image to HD resolution (1080x1920) using high-quality Lanczos resampling."""
    from PIL import Image
    
    print(f"[upscale] Upscaling {image_path.name} to {FINAL_WIDTH}x{FINAL_HEIGHT}...")
    
    # Open the image
    img = Image.open(image_path)
    original_size = img.size
    
    # Upscale using Lanczos resampling (highest quality)
    upscaled_img = img.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.Resampling.LANCZOS)
    
    # Save the upscaled image (overwrite original)
    upscaled_img.save(image_path, quality=95, optimize=True)
    
    file_size_kb = image_path.stat().st_size // 1024
    print(f"[upscale] ✅ Upscaled from {original_size[0]}x{original_size[1]} to {FINAL_WIDTH}x{FINAL_HEIGHT} ({file_size_kb}KB)")
    
    return image_path

def generate_images(scenes: list):
    """Generate unique images for each scene SEQUENTIALLY, then upscale to HD (1080x1920)"""
    print(f"[image] Generating {NUM_IMAGES} images sequentially (avoiding rate limits)...")
    
    images = []
    for i, scene in enumerate(scenes):
        # Generate image at 720x1280
        img_path = generate_image(scene, i)
        
        # Upscale to 1080x1920 for HD YouTube quality
        upscaled_path = upscale_image(img_path)
        images.append(upscaled_path)
    
    print(f"[image] ✅ All {NUM_IMAGES} images generated and upscaled to {FINAL_WIDTH}x{FINAL_HEIGHT}!")
    return images

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
Style: Default,Arial Black,16,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,5,10,10,50,1

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
        # Using FINAL_WIDTH and FINAL_HEIGHT for HD output (1080x1920)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={FINAL_WIDTH}x{FINAL_HEIGHT}:fps=30"
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
                "-vf", f"scale={FINAL_WIDTH}:{FINAL_HEIGHT}:force_original_aspect_ratio=increase,crop={FINAL_WIDTH}:{FINAL_HEIGHT},fps=30",
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
    print(f"[video] Animated slideshow saved to {ANIMATED_VIDEO} (HD {FINAL_WIDTH}x{FINAL_HEIGHT})")
    
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
