"""
Threads Upload - Enhanced Debugging Version
Uploads video to tmpfiles.org, then uses URL for Threads API
"""

import os
import sys
import requests
import time
from pathlib import Path

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def upload_to_threads(video_path, text):
    """
    Upload video to Threads via temporary public URL.
    """
    
    print("\n" + "=" * 60)
    print("🧵 THREADS UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    
    if not access_token:
        error_msg = "❌ THREADS_ACCESS_TOKEN not set"
        print(f"[threads] {error_msg}")
        raise ValueError(error_msg)
    
    if not user_id:
        error_msg = "❌ THREADS_USER_ID not set"
        print(f"[threads] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[threads] ✅ Credentials loaded")
    print(f"[threads] User ID: {user_id}")
    print(f"[threads] Token length: {len(access_token)} chars")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[threads] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[threads] ✅ Video file found: {video_path}")
    print(f"[threads] Video size: {file_size_mb:.2f} MB")
    
    # Limit text
    text_limited = text[:500] if len(text) > 500 else text
    print(f"[threads] Text length: {len(text_limited)} characters")
    
    try:
        # Step 1: Upload to tmpfiles.org to get public URL
        print(f"[threads] 📤 Step 1: Uploading to temporary hosting...")
        
        with open(video_path_obj, 'rb') as video_file:
            files = {'file': ('video.mp4', video_file, 'video/mp4')}
            temp_response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files=files,
                timeout=180
            )
        
        if temp_response.status_code != 200:
            error_msg = f"Failed to upload to temporary hosting: {temp_response.status_code}"
            print(f"[threads] ❌ {error_msg}")
            print(f"[threads] Response: {temp_response.text[:200]}")
            raise Exception(error_msg)
        
        temp_data = temp_response.json()
        if temp_data.get('status') != 'success':
            error_msg = f"Temporary hosting failed: {temp_data}"
            print(f"[threads] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # tmpfiles.org returns URL in format: https://tmpfiles.org/12345
        # We need direct download link: https://tmpfiles.org/dl/12345
        temp_url = temp_data.get('data', {}).get('url', '')
        
        # IMPORTANT: Threads might need HTTPS, not HTTP
        video_url = temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/').replace('http://', 'https://')
        
        print(f"[threads] ✅ Temporary URL created: {video_url}")
        
        # Step 2: Create Threads container with video URL
        print(f"[threads] 📦 Step 2: Creating Threads container...")
        
        # Use Instagram Graph API for Threads
        container_url = f"https://graph.facebook.com/v18.0/{user_id}/threads"
        container_params = {
            'media_type': 'VIDEO',
            'video_url': video_url,
            'text': text_limited,
            'access_token': access_token
        }
        
        print(f"[threads] Request URL: {container_url}")
        
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        print(f"[threads] Response status: {container_response.status_code}")
        
        if container_response.status_code == 200:
            response_data = container_response.json()
            container_id = response_data.get('id')
            print(f"[threads] ✅ Container created: {container_id}")
        else:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            
            print(f"[threads] ❌ Container creation failed:")
            print(f"[threads]    Error code: {error_code}")
            print(f"[threads]    Error message: {error_msg}")
            print(f"[threads]    Full response: {container_response.text[:500]}")
            
            # If this fails, Threads posting is not available for this account
            if 'not authorized' in error_msg.lower() or 'permission' in error_msg.lower():
                print(f"[threads] ℹ️  Note: Your Instagram account may not be linked to Threads")
                print(f"[threads] ℹ️  Or Threads API access is not available for your app")
            
            raise Exception(f"Threads API Error: {error_msg}")
        
        if not container_id:
            error_msg = "Failed to create container"
            print(f"[threads] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # Step 3: Wait for processing
        print(f"[threads] ⏳ Step 3: Waiting for video processing...")
        max_wait = 120
        waited = 0
        
        while waited < max_wait:
            status_url = f"https://graph.facebook.com/v18.0/{container_id}"
            status_params = {
                'fields': 'status',
                'access_token': access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_data = status_response.json()
            status = status_data.get('status', 'UNKNOWN')
            
            print(f"[threads] Status: {status} (waited {waited}s)")
            
            if status == 'FINISHED':
                print(f"[threads] ✅ Video processing complete!")
                break
            elif status == 'ERROR':
                error_msg = status_data.get('error_message', 'Video processing failed')
                print(f"[threads] ❌ {error_msg}")
                raise Exception(error_msg)
            
            time.sleep(10)
            waited += 10
        
        if waited >= max_wait:
            error_msg = "Video processing timed out"
            print(f"[threads] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # Step 4: Publish
        print(f"[threads] 📤 Step 4: Publishing to Threads...")
        publish_url = f"https://graph.facebook.com/v18.0/{user_id}/threads_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[threads] ❌ Publish failed: {error_msg}")
            raise Exception(f"Threads Publish Error: {error_msg}")
        
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
        
    except Exception as e:
        print(f"[threads] ❌ ERROR!")
        print(f"[threads] {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        try:
            result = upload_to_threads(str(video_file), "Test upload")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")
