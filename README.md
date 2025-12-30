# 🎬 YouTube Shorts Automation Bot - Ancient Women's History

Automatically generate and upload AI-powered YouTube Shorts daily about ancient women's history using GitHub Actions.

## ✨ Features

- 🤖 **AI Story Generation** - Pollinations AI creates unique Russian stories about ancient women
- 🎨 **12 Unique Scene Images** - High-quality images with Flux Turbo model (720x1280)
- 🎬 **Ken Burns Animation** - Smooth zoom effects on each image
- 🗣️ **Natural Voice Narration** - Edge-TTS with Russian Neural voices
- 📝 **Word-Level Subtitles** - UPPERCASE, synchronized using Vosk speech recognition
- 🎵 **Background Music** - Automatic mixing with narration
- 📤 **Multi-Platform Upload** - YouTube, Facebook, Instagram, Threads, Twitter, VK, TikTok
- ⚡ **Optimized Pipeline** - 8-12 minutes per video with retry logic

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd thriveruswave
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Create a `.env` file with your API keys:

```bash
# Pollinations AI (REQUIRED for story & image generation)
POLLINATIONS_API_KEY=your_api_key_here

# YouTube Upload
YT_CLIENT_ID=your_client_id
YT_CLIENT_SECRET=your_client_secret
YT_REFRESH_TOKEN=your_refresh_token

# Facebook/Instagram/Threads (Meta Platforms)
META_ACCESS_TOKEN=your_permanent_token
META_PAGE_ID=your_page_id
INSTAGRAM_ACCOUNT_ID=your_instagram_id
THREADS_ACCOUNT_ID=your_threads_id

# Twitter/X
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# VK (Vkontakte)
VK_ACCESS_TOKEN=your_vk_token
VK_GROUP_ID=your_group_id

# TikTok (Optional)
TIKTOK_ACCESS_TOKEN=your_tiktok_token
```

### 3. Add Your Music

```bash
# Copy your background music to:
audio/music.mp3
```

### 4. Generate Topics

```bash
python generate_topics.py
# This creates topics.txt with 100+ unique topics
```

### 5. Test Locally

```bash
python main.py
# Video will be in: output/final_video.mp4
```

### 6. Upload to Platforms

```bash
python upload_all_platforms.py
# Uploads to all configured platforms
```

---

## 📊 Performance & Specifications

| Metric | Value |
|--------|-------|
| Generation Time | 8-12 minutes |
| Video Quality | 720x1280, CRF 18 (high) |
| File Size | 10-15 MB |
| Images per Video | 12 unique scenes |
| Story Length | 80-130 words (~30-40 seconds) |
| Monthly GitHub Actions | ~400 min (free tier: 2,000) |
| YouTube Uploads/Day | ~6 (quota limit) |

---

## 🎨 Quality Features

### Image Generation
- **Resolution**: 720x1280 (safer for Turbo model, prevents double faces)
- **Model**: Flux Turbo via Pollinations AI
- **Unique Seeds**: Each image has unique seed based on scene + index
- **Realistic Style**: Raw analog photo aesthetic with ancient gold theme
- **Safety**: Strict negative prompts to ensure SFW content
- **Features**: Extreme close-up portraits, stunning hair, gold jewelry, glistening skin

### Video Production
- **High Bitrate Encoding**: CRF 18 for excellent quality
- **Smooth Animations**: Ken Burns zoom effects (alternating in/out)
- **Professional Subtitles**: Arial Black, bold, centered, word-by-word sync
- **Audio Mixing**: Balanced narration + background music (25% volume)

### Retry Logic
- **Story Generation**: 3 retries with 30s, 1min, 2min delays
- **Image Generation**: 5 retries with 10s, 20s, 30s, 1min, 2min delays
- **Robust Error Handling**: Handles 502, 524, timeout errors gracefully

---

## 📁 Project Structure

```
├── main.py                      # Main video generation pipeline
├── upload_all_platforms.py      # Multi-platform upload orchestrator
├── upload_to_youtube.py         # YouTube upload script
├── upload_facebook.py           # Facebook upload script
├── upload_instagram.py          # Instagram upload script
├── upload_threads.py            # Threads upload script
├── upload_twitter.py            # Twitter/X upload script
├── upload_vk.py                 # VK upload script
├── upload_tiktok.py             # TikTok upload script
├── generate_topics.py           # AI-powered topic generator
├── get_youtube_token.py         # YouTube OAuth helper
├── requirements.txt             # Python dependencies
├── topics.txt                   # Story topics queue (FIFO)
├── README.md                    # This file
├── audio/
│   └── music.mp3               # Your background music
├── .github/workflows/
│   └── daily-shorts.yml        # GitHub Actions workflow
├── images/                     # Generated images (auto-created)
└── output/                     # Generated videos (auto-created)
    ├── story.txt               # Generated story
    ├── scenes.txt              # Scene descriptions
    ├── narration.mp3           # TTS audio
    ├── subtitles.ass           # Word-level subtitles
    └── final_video.mp4         # Final output
```

---

## ⚙️ Configuration

### Change Number of Images

Edit `main.py`:
```python
NUM_IMAGES = 12  # 6-15 recommended (12 is optimal)
```

### Change Image Resolution

Edit `main.py`:
```python
IMAGE_WIDTH = 720    # 720 or 1080
IMAGE_HEIGHT = 1280  # 1280 or 1920
```

### Change Story Length

Edit `main.py`:
```python
STORY_MAX_WORDS = 130  # 80-150 recommended
```

### Change Upload Schedule

Edit `.github/workflows/daily-shorts.yml`:
```yaml
schedule:
  - cron: "0 6 * * *"  # 6 AM UTC daily
```

### Add More Topics

Edit `topics.txt` or run:
```bash
python generate_topics.py
```

---

## 🔧 API Setup Guides

### Pollinations AI (REQUIRED)

1. Visit https://enter.pollinations.ai
2. Sign up for paid API access
3. Get your API key
4. Add to `.env`: `POLLINATIONS_API_KEY=your_key`

**Cost**: ~$0.01-0.02 per video (story + 12 images)

### YouTube Upload

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `client_secrets.json`
6. Run `python get_youtube_token.py` to authenticate
7. Add credentials to `.env` or GitHub Secrets

**Required Secrets**:
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

### Meta Platforms (Facebook/Instagram/Threads)

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create an app with "Business" type
3. Add "Instagram Graph API" and "Facebook Graph API"
4. Get a permanent access token (60-day or never-expiring)
5. Get your Page ID, Instagram Account ID, Threads Account ID

**Required Secrets**:
- `META_ACCESS_TOKEN` (permanent token)
- `META_PAGE_ID`
- `INSTAGRAM_ACCOUNT_ID`
- `THREADS_ACCOUNT_ID`

### Twitter/X

1. Go to [Twitter Developer Portal](https://developer.twitter.com)
2. Create a new app with Read & Write permissions
3. Generate API keys and access tokens
4. Enable OAuth 1.0a

**Required Secrets**:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`

### VK (Vkontakte)

1. Create a VK community/group
2. Use Kate Mobile method to get access token:
   - Visit: https://oauth.vk.com/authorize?client_id=2685278&scope=1073737727&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1
   - Login and authorize
   - Copy token from URL
3. Get your group ID (negative number)

**Required Secrets**:
- `VK_ACCESS_TOKEN`
- `VK_GROUP_ID`

### TikTok (Optional)

1. Go to [TikTok for Developers](https://developers.tiktok.com)
2. Create an app
3. Get access token (complex OAuth flow)

**Required Secrets**:
- `TIKTOK_ACCESS_TOKEN`

---

## 🤖 GitHub Actions Setup

### 1. Add Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add all the secrets from the `.env` file above.

### 2. Enable Workflow

1. Push your code to GitHub
2. Go to Actions tab
3. Enable workflows
4. The workflow runs daily at 6 AM UTC

### 3. Manual Trigger

You can also trigger manually:
- Go to Actions tab
- Select "Daily YouTube Shorts"
- Click "Run workflow"

---

## 📝 How It Works

### Video Generation Pipeline

1. **Topic Selection** (FIFO Queue)
   - Reads first topic from `topics.txt`
   - Removes it from the file (queue system)

2. **Story Generation** (Pollinations AI)
   - Uses Mistral model for Russian text
   - Generates 80-130 word story
   - 3 retry attempts with exponential backoff

3. **Scene Extraction**
   - Splits story into sentences
   - Creates 12 unique scene descriptions
   - Adds visual variations

4. **Image Generation** (Pollinations AI)
   - Translates scenes to English for better API stability
   - Generates 12 unique images with Flux Turbo
   - Each image has unique seed (hash of scene + index)
   - 5 retry attempts per image
   - 2-second delay between successful requests

5. **TTS Narration** (Edge-TTS)
   - Converts story to Russian speech
   - Uses Dmitry Neural voice (male)
   - Free Microsoft TTS

6. **Subtitle Generation** (Vosk)
   - Downloads Russian model (~50 MB, one-time)
   - Converts MP3 to WAV
   - Generates word-level timestamps
   - Creates ASS subtitle file with UPPERCASE text

7. **Animation** (FFmpeg)
   - Creates Ken Burns zoom effects
   - Alternates zoom in/out for variety
   - Matches audio duration
   - High quality encoding (CRF 18)

8. **Composition** (FFmpeg)
   - Overlays subtitles on video
   - Merges narration + background music
   - Final output: 720x1280 MP4

9. **Multi-Platform Upload**
   - Uploads to all configured platforms
   - Generates dynamic descriptions/tags
   - Reports success/failure for each platform

---

## 🔧 Troubleshooting

### Video Quality Issues

**Problem**: Blurry or low-quality images
- **Solution**: Images are 720x1280 to prevent double faces with Turbo model
- **Alternative**: Use 1080x1920 with a different model (may cost more)

**Problem**: Deformed faces or double heads
- **Solution**: Already using strict negative prompts and 720p resolution
- **Check**: Verify each image is unique (different file sizes)

### API Errors

**Problem**: 502/524 errors from Pollinations AI
- **Solution**: Retry logic is already implemented (5 retries per image)
- **Wait**: Paid API should be more reliable, but peak times may still fail
- **Check**: Verify your API key is valid and has credits

**Problem**: Story generation fails
- **Solution**: 3 retry attempts with delays
- **Check**: Verify `POLLINATIONS_API_KEY` is set correctly

### Upload Failures

**Problem**: YouTube upload fails
- **Solution**: Check quota limits (6 uploads/day for free tier)
- **Verify**: `YT_REFRESH_TOKEN` is valid
- **Regenerate**: Run `python get_youtube_token.py` again

**Problem**: Meta platforms fail
- **Solution**: Ensure token is permanent (not 60-day)
- **Check**: Page ID and Account IDs are correct
- **Verify**: App has correct permissions

**Problem**: Twitter upload fails
- **Solution**: Ensure app has Read & Write permissions
- **Check**: OAuth 1.0a is enabled
- **Verify**: All 4 credentials are correct

### Slow Generation

**Problem**: Takes too long to generate video
- **Solution**: Reduce `NUM_IMAGES` to 8-10
- **Note**: Images are the slowest part (~10-30 sec each with retries)
- **Optimize**: Paid API should be faster than free tier

### Subtitle Issues

**Problem**: Subtitles not synchronized
- **Solution**: Vosk generates word-level timestamps automatically
- **Check**: Verify `vosk-model-small-ru-0.22` is downloaded
- **Alternative**: Use a larger Vosk model for better accuracy

---

## 📈 Optimization Tips

### Cost Optimization

1. **Use Paid API**: More reliable, faster, fewer retries needed
2. **Reduce Images**: 8-10 images instead of 12 saves ~20% cost
3. **Batch Generation**: Generate multiple videos at once (if API allows)

### Quality Optimization

1. **Higher Resolution**: Use 1080x1920 for better quality (may increase double-face risk)
2. **Better Model**: Try different Pollinations models (may cost more)
3. **Longer Stories**: Increase `STORY_MAX_WORDS` to 150-200
4. **More Images**: Increase `NUM_IMAGES` to 15-20 for smoother transitions

### Speed Optimization

1. **Parallel Processing**: Generate images in parallel (risk of rate limits)
2. **Reduce Retries**: Lower retry counts (risk of failures)
3. **Smaller Model**: Use smaller Vosk model (faster but less accurate)

---

## 🎯 Best Practices

### Topic Generation

- Generate 100+ topics at once with `generate_topics.py`
- Mix generic and specific topics
- Focus on interesting, lesser-known historical facts
- Avoid controversial or sensitive topics

### Image Prompts

- Keep prompts detailed but concise
- Use negative prompts to prevent unwanted content
- Test different seeds if images are too similar
- Ensure SFW compliance with strict negative prompts

### Video Titles

- Use first sentence of story for relevance
- Keep under 60 characters for mobile
- Add context if title is too short
- Use Russian for target audience

### Descriptions & Tags

- Use relevant hashtags (#Shorts, #История, etc.)
- Keep descriptions short for Shorts format
- Avoid mentioning AI tools (as per user preference)
- Use platform-specific best practices

---

## 📊 Monitoring & Analytics

### GitHub Actions Logs

- Check Actions tab for workflow status
- Review logs for errors or warnings
- Monitor execution time (should be 8-12 min)

### Platform Analytics

- **YouTube**: Check YouTube Studio for views, retention
- **Facebook**: Check Page Insights
- **Instagram**: Check Instagram Insights
- **Twitter**: Check Twitter Analytics
- **VK**: Check Community Statistics

### Cost Tracking

- Monitor Pollinations AI usage/credits
- Track API costs per video
- Estimate monthly costs based on upload frequency

---

## 🚨 Important Notes

### API Quotas

- **YouTube**: 10,000 units/day (1 upload = ~1,600 units = ~6 uploads/day)
- **Meta**: Rate limits vary by endpoint
- **Twitter**: 50 tweets/day for free tier
- **Pollinations**: Based on your paid plan

### Content Safety

- All images use strict SFW negative prompts
- No nudity, explicit content, or NSFW material
- Cleavage acceptable, but no exposed breasts
- Focus on historical accuracy and education

### Token Expiration

- **YouTube**: Refresh tokens don't expire (unless revoked)
- **Meta**: Permanent tokens can be 60-day or never-expiring
- **Twitter**: Tokens don't expire (unless revoked)
- **VK**: Tokens may expire, use Kate Mobile method for long-lived tokens

---

## 📄 License

MIT License - Feel free to modify and use!

---

## 🙏 Credits

- **Pollinations AI** - Story & image generation (Mistral, Flux Turbo)
- **Vosk** - Word-level subtitle generation
- **Edge-TTS** - Voice narration (Microsoft Neural voices)
- **FFmpeg** - Video processing and composition

---

## 🆘 Support

If you encounter issues:

1. Check this README for troubleshooting
2. Review GitHub Actions logs
3. Verify all API keys and credentials
4. Test locally before deploying to GitHub Actions
5. Check API status pages for outages

---

## 🎉 Success Checklist

- [ ] Pollinations API key obtained and tested
- [ ] Topics generated (100+ in topics.txt)
- [ ] Background music added (audio/music.mp3)
- [ ] Local video generation tested successfully
- [ ] YouTube credentials configured
- [ ] Meta platforms configured (optional)
- [ ] Twitter configured (optional)
- [ ] VK configured (optional)
- [ ] GitHub Secrets added
- [ ] GitHub Actions workflow enabled
- [ ] First automated upload successful
- [ ] Monitoring setup for analytics

---

**Happy Automating! 🚀**
