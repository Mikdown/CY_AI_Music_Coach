#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/miked/CY_AI_Music_Coach')

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API key
youtube_key = os.getenv("YOUTUBE_API_KEY")
print(f"YouTube API Key present: {bool(youtube_key)}")
if youtube_key:
    print(f"Key length: {len(youtube_key)}")
    print(f"First 10 chars: {youtube_key[:10]}...")
else:
    print("⚠️  YOUTUBE_API_KEY not found in environment")

# Try importing
try:
    from youtube_search_API import initialize_youtube_client, search_youtube_videos
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Initialize
print("\n🔄 Initializing YouTube client...")
youtube_client = initialize_youtube_client()
print(f"Client initialized: {youtube_client is not None}")

if youtube_client:
    # Try a simple search
    print("\n🔍 Testing search for 'beginner guitar lessons'...")
    try:
        results = search_youtube_videos("beginner guitar lessons", youtube_client, max_results=5)
        print(f"✅ Found {len(results)} videos")
        if results:
            print("\nFirst 3 videos:")
            for i, video in enumerate(results[:3], 1):
                print(f"\n{i}. {video['title']}")
                print(f"   URL: {video['url']}")
                print(f"   Views: {video['views']:,}")
                print(f"   Channel: {video['channel']}")
        else:
            print("⚠️  No videos returned - all filtered out")
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Could not initialize YouTube client - check API key")
