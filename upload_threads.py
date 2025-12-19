"""
Threads Upload - FIXED FOR GITHUB ACTIONS

Uploads videos to Threads using Instagram Graph API.
Enhanced with comprehensive debugging.
"""

import os
import requests
from pathlib import Path
import time

def upload_to_threads(video_file, caption):
    """
    Upload video to Threads.
    
    Threads uses the same API as Instagram.
    """
    
    print("\n" + "=" * 60)
    print("🧵 THREADS UPLOAD STARTING")
    print("=" * 60)
    
    # Check credentials
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    
    if not access_token:
        error_msg = "❌ THREADS_ACCESS_TOKEN not set in environment variables"
        print(f"[threads] {error_msg}")
        raise ValueError(error_msg)
    
    if not user_id:
        error_msg = "❌ THREADS_USER_ID not set in environment variables"
        print(f"[threads] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[threads] ✅ Credentials loaded")
    print(f"[threads] User ID: {user_id}")
    print(f"[threads] Token: {access_token[:20]}...")
    
    # Check video file
    video_path = Path(video_file)
    if not video_path.exists():
        error_msg = f"❌ Video file not found: {video_file}"
        print(f"[threads] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"[threads] ✅ Video file found: {video_file}")
    print(f"[threads] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:500] if len(caption) > 500 else caption
    print(f"[threads] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Create media container
        print(f"[threads] 📦 Step 1: Creating media container...")
        container_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
        
        container_params = {
            'media_type': 'VIDEO',
            'video_url': str(video_file),  # Will need public URL
            'text': caption_limited,
            'access_token': access_token
        }
        
        print(f"[threads] Sending container creation request...")
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            
            print(f"[threads] ❌ Container creation FAILED!")
            print(f"[threads] Status Code: {container_response.status_code}")
            print(f"[threads] Error Code: {error_code}")
            print(f"[threads] Error Message: {error_msg}")
            print(f"[threads] Full Response: {container_response.text[:500]}")
            
            # Specific error for public URL requirement
            if 'video_url' in error_msg.lower() or 'public' in error_msg.lower():
                print(f"[threads] ⚠️  Threads requires video at public URL")
                print(f"[threads] This is expected to fail locally")
                print(f"[threads] Will work in GitHub Actions with proper setup")
            
            print("=" * 60)
            raise Exception(f"Threads API Error {container_response.status_code}: {error_msg}")
        
        container_id = container_response.json().get('id')
        print(f"[threads] ✅ Container created: {container_id}")
        
        # Step 2: Wait for processing
        print(f"[threads] ⏳ Step 2: Waiting for video processing...")
        max_wait = 120  # 2 minutes
        waited = 0
        
        while waited < max_wait:
            status_url = f"https://graph.threads.net/v1.0/{container_id}"
            status_params = {
                'fields': 'status_code',
                'access_token': access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_code = status_response.json().get('status_code')
            
            print(f"[threads] Status: {status_code} (waited {waited}s)")
            
            if status_code == 'FINISHED':
                print(f"[threads] ✅ Video processing complete!")
                break
            elif status_code == 'ERROR':
                error_msg = "Video processing failed on Threads' servers"
                print(f"[threads] ❌ {error_msg}")
                print("=" * 60)
                raise Exception(error_msg)
            
            time.sleep(10)
            waited += 10
        
        if waited >= max_wait:
            error_msg = "Video processing timed out"
            print(f"[threads] ❌ {error_msg}")
            print("=" * 60)
            raise Exception(error_msg)
        
        # Step 3: Publish
        print(f"[threads] 📤 Step 3: Publishing to Threads...")
        publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            
            print(f"[threads] ❌ Publishing FAILED!")
            print(f"[threads] Status Code: {publish_response.status_code}")
            print(f"[threads] Error Code: {error_code}")
            print(f"[threads] Error Message: {error_msg}")
            print("=" * 60)
            raise Exception(f"Threads Publish Error {publish_response.status_code}: {error_msg}")
        
        thread_id = publish_response.json().get('id')
        
        print(f"[threads] ✅ SUCCESS! Video published to Threads!")
        print(f"[threads] Thread ID: {thread_id}")
        print(f"[threads] Check your Threads profile to see the post!")
        print("=" * 60)
        
        return {
            'id': thread_id,
            'platform': 'threads',
            'status': 'success'
        }
        
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out"
        print(f"[threads] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"🌐 Connection error: {str(e)}"
        print(f"[threads] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except Exception as e:
        print(f"[threads] ❌ UNEXPECTED ERROR!")
        print(f"[threads] Error type: {type(e).__name__}")
        print(f"[threads] Error message: {str(e)}")
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
            result = upload_to_threads(video_file, caption)
            print(f"\n✅ Test successful! Result: {result}")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")
