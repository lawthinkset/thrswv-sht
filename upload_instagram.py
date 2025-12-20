"""
Instagram Reels Upload - FIXED with file.io

Uses temporary file hosting (file.io) to provide public URL for Instagram.
This is compliant with Instagram's API requirements.

file.io is a free, privacy-focused service:
- Auto-deletes after download
- No account needed
- GDPR compliant
- No tracking
"""

import os
import requests
import time
from pathlib import Path

def upload_to_fileio(video_path):
    """
    Upload video to file.io and get public URL.
    
    file.io is a free, temporary file hosting service.
    Files auto-delete after first download.
    """
    print(f"[instagram] 📤 Uploading video to file.io for temporary hosting...")
    
    try:
        with open(video_path, 'rb') as f:
            response = requests.post(
                'https://file.io',
                files={'file': f},
                data={'expires': '1h'},  # Auto-delete after 1 hour
                timeout=120
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                public_url = result.get('link')
                print(f"[instagram] ✅ Video uploaded to file.io")
                print(f"[instagram] Public URL: {public_url[:50]}...")
                return public_url
            else:
                raise Exception(f"file.io upload failed: {result.get('message', 'Unknown error')}")
        else:
            raise Exception(f"file.io returned status {response.status_code}")
            
    except Exception as e:
        print(f"[instagram] ❌ file.io upload failed: {e}")
        raise

def upload_to_instagram(video_file, caption):
    """
    Upload video to Instagram Reels.
    
    Uses file.io for temporary hosting to provide public URL.
    """
    
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM UPLOAD STARTING")
    print("=" * 60)
    
    # Check credentials
    access_token = os.getenv('IG_ACCESS_TOKEN')
    user_id = os.getenv('IG_USER_ID')
    
    if not access_token:
        error_msg = "❌ IG_ACCESS_TOKEN not set in environment variables"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    if not user_id:
        error_msg = "❌ IG_USER_ID not set in environment variables"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[instagram] ✅ Credentials loaded")
    print(f"[instagram] User ID: {user_id}")
    print(f"[instagram] Token: {access_token[:20]}...")
    
    # Check video file
    video_path = Path(video_file)
    if not video_path.exists():
        error_msg = f"❌ Video file not found: {video_file}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_file}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Upload to file.io to get public URL
        print(f"[instagram] 📦 Step 1: Getting public URL via file.io...")
        public_url = upload_to_fileio(video_file)
        
        # Step 2: Create Instagram container with public URL
        print(f"[instagram] 📦 Step 2: Creating Instagram media container...")
        container_url = f"https://graph.facebook.com/v24.0/{user_id}/media"
        
        container_params = {
            'media_type': 'REELS',
            'video_url': public_url,  # Use public URL from file.io
            'caption': caption_limited,
            'share_to_feed': 'true',
            'access_token': access_token
        }
        
        print(f"[instagram] Sending container creation request...")
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            
            print(f"[instagram] ❌ Container creation FAILED!")
            print(f"[instagram] Status Code: {container_response.status_code}")
            print(f"[instagram] Error Code: {error_code}")
            print(f"[instagram] Error Message: {error_msg}")
            print(f"[instagram] Full Response: {container_response.text[:500]}")
            print("=" * 60)
            raise Exception(f"Instagram API Error {container_response.status_code}: {error_msg}")
        
        container_id = container_response.json().get('id')
        print(f"[instagram] ✅ Container created: {container_id}")
        
        # Step 3: Wait for processing
        print(f"[instagram] ⏳ Step 3: Waiting for video processing...")
        max_wait = 180  # 3 minutes (file.io download + processing)
        waited = 0
        
        while waited < max_wait:
            status_url = f"https://graph.facebook.com/v24.0/{container_id}"
            status_params = {
                'fields': 'status_code',
                'access_token': access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_code = status_response.json().get('status_code')
            
            print(f"[instagram] Status: {status_code} (waited {waited}s)")
            
            if status_code == 'FINISHED':
                print(f"[instagram] ✅ Video processing complete!")
                break
            elif status_code == 'ERROR':
                error_msg = "Video processing failed on Instagram's servers"
                print(f"[instagram] ❌ {error_msg}")
                print(f"[instagram] This might be due to video format/codec issues")
                print("=" * 60)
                raise Exception(error_msg)
            
            time.sleep(15)  # Check every 15 seconds
            waited += 15
        
        if waited >= max_wait:
            error_msg = "Video processing timed out"
            print(f"[instagram] ❌ {error_msg}")
            print("=" * 60)
            raise Exception(error_msg)
        
        # Step 4: Publish
        print(f"[instagram] 📤 Step 4: Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v24.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            
            print(f"[instagram] ❌ Publishing FAILED!")
            print(f"[instagram] Status Code: {publish_response.status_code}")
            print(f"[instagram] Error Code: {error_code}")
            print(f"[instagram] Error Message: {error_msg}")
            print("=" * 60)
            raise Exception(f"Instagram Publish Error {publish_response.status_code}: {error_msg}")
        
        media_id = publish_response.json().get('id')
        
        print(f"[instagram] ✅ SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print(f"[instagram] Check your Instagram profile to see the Reel!")
        print("=" * 60)
        
        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }
        
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out"
        print(f"[instagram] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"🌐 Connection error: {str(e)}"
        print(f"[instagram] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except Exception as e:
        print(f"[instagram] ❌ UNEXPECTED ERROR!")
        print(f"[instagram] Error type: {type(e).__name__}")
        print(f"[instagram] Error message: {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    # Test upload
    from pathlib import Path
    
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        story_file = Path('output/story.txt')
        caption = story_file.read_text(encoding='utf-8') if story_file.exists() else "Test upload"
        
        try:
            result = upload_to_instagram(video_file, caption)
            print(f"\n✅ Test successful! Result: {result}")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")
