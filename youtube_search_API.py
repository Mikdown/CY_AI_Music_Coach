"""
YouTube Data API wrapper for searching guitar-related videos
based on user assessment responses.
"""

import os
from typing import List, Dict
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv


def initialize_youtube_client():
    """
    Initialize the YouTube API client.
    Requires YOUTUBE_API_KEY in environment variables.
    
    Returns:
        YouTube API client or None if key is not available
    """
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        print("⚠️  YOUTUBE_API_KEY not found. YouTube search functionality disabled.")
        return None
    
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        print("✅ YouTube API client initialized")
        return youtube
    except HttpError as e:
        print(f"❌ Error initializing YouTube API: {e}")
        return None


def get_video_details_batch(
    video_ids: List[str],
    youtube_client
) -> Dict[str, Dict]:
    """
    Get detailed information for multiple videos in a batch.
    Validates videos using proper YouTube API status fields.
    
    Args:
        video_ids: List of YouTube video IDs
        youtube_client: YouTube API client
        
    Returns:
        Dict mapping video_id to detailed video information
    """
    if not youtube_client or not video_ids:
        return {}
    
    try:
        # Process in batches of 50 (YouTube API limit)
        video_details = {}
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            # Batch request for detailed video info
            request = youtube_client.videos().list(
                part="snippet,contentDetails,statistics,status",
                id=",".join(batch_ids)
            )
            response = request.execute()
            
            for item in response.get("items", []):
                video_id = item["id"]
                try:
                    stats = item.get("statistics", {})
                    status = item.get("status", {})
                    content_details = item.get("contentDetails", {})
                    
                    # Check privacy status - CRITICAL for availability
                    privacy_status = status.get("privacyStatus", "").lower()
                    if privacy_status not in ["public"]:
                        print(f"⚠️  Skipping {video_id}: privacyStatus={privacy_status} (not public)")
                        continue
                    
                    # Check for region restrictions
                    region_restriction = content_details.get("regionRestriction", {})
                    blocked_regions = region_restriction.get("blocked", [])
                    allowed_regions = region_restriction.get("allowed", [])
                    
                    # If allowed list exists and is not empty, user's region must be in it
                    # We'll be conservative and skip videos with region restrictions
                    has_region_restriction = bool(region_restriction)
                    if has_region_restriction:
                        print(f"⚠️  Skipping {video_id}: has region restrictions")
                        continue
                    
                    # Check embeddable status
                    is_embeddable = status.get("embeddable", False)
                    if not is_embeddable:
                        print(f"⚠️  Skipping {video_id}: not embeddable")
                        continue
                    
                    # Check view count for meaningful content
                    views = int(stats.get("viewCount", 0))
                    if views < 100:
                        print(f"⚠️  Skipping {video_id}: views={views} (< 100 views)")
                        continue
                    
                    # Video passed all checks
                    published_at = datetime.fromisoformat(
                        item["snippet"]["publishedAt"].replace("Z", "+00:00")
                    )
                    likes = int(stats.get("likeCount", 0))
                    
                    video_details[video_id] = {
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "description": item["snippet"]["description"],
                        "published_at": item["snippet"]["publishedAt"],
                        "duration": item["contentDetails"]["duration"],
                        "views": views,
                        "likes": likes,
                        "privacy_status": privacy_status,
                        "is_embeddable": is_embeddable,
                        "is_available": True
                    }
                    print(f"✅ Valid video: {video_id} - {item['snippet']['title'][:60]}...")
                    
                except Exception as e:
                    print(f"Error processing video {video_id}: {e}")
                    continue
        
        return video_details
    except HttpError as e:
        print(f"❌ YouTube API error fetching details: {e}")
        return {}


def search_youtube_videos(
    query: str,
    youtube_client,
    max_results: int = 10
) -> List[Dict]:
    """
    Search for YouTube videos matching the given query with strict validation.
    Only returns videos that are confirmed available, embeddable, and have significant engagement.
    
    Args:
        query: Search query string
        youtube_client: YouTube API client
        max_results: Maximum number of initial results to check (will filter to valid ones)
        
    Returns:
        List of validated video results with title, link, channel, and description
    """
    if not youtube_client:
        print("❌ YouTube client not initialized")
        return []
    
    try:
        print(f"🔍 Searching YouTube for: {query}")
        # Search with higher count to account for filtering
        request = youtube_client.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=min(max_results * 5, 50),  # Request up to 5x to account for filtering
            relevanceLanguage="en",
            order="viewCount",  # Most important: sort by actual view count
            videoCaption="any"  # Prefer videos with captions
        )
        response = request.execute()
        
        search_results = response.get("items", [])
        print(f"📺 Found {len(search_results)} initial results")
        
        video_ids = [item["id"]["videoId"] for item in search_results]
        
        if not video_ids:
            print("⚠️  No videos found in search results")
            return []
        
        # Batch fetch video details to validate them
        video_details = get_video_details_batch(video_ids, youtube_client)
        print(f"📊 Fetched details for {len(video_details)} videos")
        
        # Filter and format valid videos
        valid_videos = []
        for item in search_results:
            video_id = item["id"]["videoId"]
            details = video_details.get(video_id, {})
            
            # Only include videos that pass ALL checks
            if details and details.get("is_available"):
                video = {
                    "title": item["snippet"]["title"],
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": item["snippet"]["channelTitle"],
                    "description": item["snippet"]["description"],
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                    "views": details.get("views", 0),
                    "likes": details.get("likes", 0),
                    "published_at": details.get("published_at", ""),
                    "status": "available"
                }
                valid_videos.append(video)
                print(f"✅ Valid: '{video['title'][:50]}...' ({video['views']:,} views)")
        
        print(f"✅ Returning {len(valid_videos)} validated videos out of {len(search_results)} found")
        
        # Sort by view count (most relevant first)
        valid_videos.sort(key=lambda x: x["views"], reverse=True)
        
        return valid_videos
        
    except HttpError as e:
        print(f"❌ YouTube API error: {e}")
        if "invalid_request" in str(e).lower():
            print("⚠️  Check if YOUTUBE_API_KEY is valid and has quota")
        return []
    except Exception as e:
        print(f"❌ Unexpected error in search: {e}")
        return []


def search_by_assessment_answers(
    assessment_answers: Dict[str, str],
    youtube_client,
    videos_per_topic: int = 3
) -> Dict[str, List[Dict]]:
    """
    Search YouTube for videos based on the 5 assessment answers.
    Ensures all returned videos are available and valid.
    
    Args:
        assessment_answers: Dict with keys:
            - guitar_type: Type of guitar (e.g., "acoustic", "electric")
            - skill_level: Skill level (e.g., "beginner", "intermediate", "advanced")
            - genre: Music genre (e.g., "blues", "rock", "jazz")
            - session_focus: Session focus area (e.g., "finger dexterity", "chord transitions")
            - mood: Mood preference (e.g., "energetic", "relaxed", "focused")
        youtube_client: YouTube API client
        videos_per_topic: Number of videos to return per assessment answer
        
    Returns:
        Dict with assessment keys mapped to lists of valid video results
    """
    results = {}
    
    # Define search queries based on assessment answers with additional filters
    search_queries = {
        "guitar_type": f"{assessment_answers.get('guitar_type', 'guitar')} guitar techniques tutorial",
        "skill_level": f"{assessment_answers.get('skill_level', 'beginner')} guitar lessons",
        "genre": f"{assessment_answers.get('genre', 'rock')} guitar tutorial",
        "session_focus": f"guitar {assessment_answers.get('session_focus', 'practice')} exercise",
        "mood": f"{assessment_answers.get('mood', 'upbeat')} guitar practice session"
    }
    
    # Search for videos for each assessment answer
    for key, query in search_queries.items():
        print(f"🔍 Searching for: {query}")
        # Request more results to account for filtering
        videos = search_youtube_videos(
            query, 
            youtube_client, 
            max_results=min(videos_per_topic * 3, 50)
        )
        # Take only the requested number of valid videos
        results[key] = videos[:videos_per_topic]
    
    return results


def format_search_results(search_results: Dict[str, List[Dict]]) -> str:
    """
    Format YouTube search results for display.
    
    Args:
        search_results: Results from search_by_assessment_answers
        
    Returns:
        Formatted string with video links and information
    """
    if not search_results or all(len(v) == 0 for v in search_results.values()):
        return "No YouTube videos found. Please ensure YOUTUBE_API_KEY is configured."
    
    output = "🎸 **YouTube Learning Resources**\n\n"
    
    category_names = {
        "guitar_type": "Guitar Type Training",
        "skill_level": "Skill Level Lessons",
        "genre": "Genre-Specific Techniques",
        "session_focus": "Focus Area Exercises",
        "mood": "Practice Mood"
    }
    
    for category, category_name in category_names.items():
        videos = search_results.get(category, [])
        
        if videos:
            output += f"**{category_name}**\n"
            for i, video in enumerate(videos, 1):
                output += f"{i}. [{video['title']}]({video['url']})\n"
                output += f"   Channel: {video['channel']}\n"
                if video.get('views'):
                    output += f"   Views: {video['views']:,}\n"
            output += "\n"
    
    return output


def get_video_details(video_id: str, youtube_client) -> Dict:
    """
    Get detailed information about a specific video with proper availability checks.
    
    Args:
        video_id: YouTube video ID
        youtube_client: YouTube API client
        
    Returns:
        Dict with detailed video information including duration, or empty dict if unavailable
    """
    if not youtube_client:
        return {}
    
    try:
        request = youtube_client.videos().list(
            part="snippet,contentDetails,statistics,status",
            id=video_id
        )
        response = request.execute()
        
        if response.get("items"):
            item = response["items"][0]
            stats = item.get("statistics", {})
            status = item.get("status", {})
            content_details = item.get("contentDetails", {})
            
            # Check privacy status - CRITICAL
            privacy_status = status.get("privacyStatus", "").lower()
            if privacy_status != "public":
                print(f"⚠️  Video {video_id} not public: privacyStatus={privacy_status}")
                return {}
            
            # Check for region restrictions
            region_restriction = content_details.get("regionRestriction", {})
            if region_restriction:
                print(f"⚠️  Video {video_id} has region restrictions")
                return {}
            
            # Check embeddable
            is_embeddable = status.get("embeddable", False)
            if not is_embeddable:
                print(f"⚠️  Video {video_id} is not embeddable")
                return {}
            
            # Check view count
            views = int(stats.get("viewCount", 0))
            if views < 100:
                print(f"⚠️  Video {video_id} has insufficient views ({views})")
                return {}
            
            return {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": item["contentDetails"]["duration"],
                "views": views,
                "likes": int(stats.get("likeCount", 0)),
                "description": item["snippet"]["description"],
                "published_at": item["snippet"]["publishedAt"],
                "privacy_status": privacy_status,
                "is_available": True
            }
        return {}
    except HttpError as e:
        print(f"❌ Error fetching video details: {e}")
        return {}

