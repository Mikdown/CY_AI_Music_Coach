"""
YouTube Data API wrapper for searching guitar-related videos
based on user assessment responses.
"""

import os
from typing import List, Dict
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


def search_youtube_videos(
    query: str,
    youtube_client,
    max_results: int = 5
) -> List[Dict]:
    """
    Search for YouTube videos matching the given query.
    
    Args:
        query: Search query string
        youtube_client: YouTube API client
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        List of video results with title, link, channel, and description
    """
    if not youtube_client:
        return []
    
    try:
        request = youtube_client.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            relevanceLanguage="en",
            order="relevance"
        )
        response = request.execute()
        
        videos = []
        for item in response.get("items", []):
            video = {
                "title": item["snippet"]["title"],
                "video_id": item["id"]["videoId"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "channel": item["snippet"]["channelTitle"],
                "description": item["snippet"]["description"],
                "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
            }
            videos.append(video)
        
        return videos
    except HttpError as e:
        print(f"❌ YouTube API error: {e}")
        return []


def search_by_assessment_answers(
    assessment_answers: Dict[str, str],
    youtube_client,
    videos_per_topic: int = 3
) -> Dict[str, List[Dict]]:
    """
    Search YouTube for videos based on the 5 assessment answers.
    
    Args:
        assessment_answers: Dict with keys:
            - guitar_type: Type of guitar (e.g., "acoustic", "electric")
            - skill_level: Skill level (e.g., "beginner", "intermediate", "advanced")
            - genre: Music genre (e.g., "blues", "rock", "jazz")
            - session_focus: Session focus area (e.g., "finger dexterity", "chord transitions")
            - mood: Mood preference (e.g., "energetic", "relaxed", "focused")
        youtube_client: YouTube API client
        videos_per_topic: Number of videos to fetch per assessment answer
        
    Returns:
        Dict with assessment keys mapped to lists of video results
    """
    results = {}
    
    # Define search queries based on assessment answers
    search_queries = {
        "guitar_type": f"{assessment_answers.get('guitar_type', 'guitar')} guitar techniques tutorial",
        "skill_level": f"{assessment_answers.get('skill_level', 'beginner')} guitar lessons",
        "genre": f"{assessment_answers.get('genre', 'rock')} guitar tutorial",
        "session_focus": f"guitar {assessment_answers.get('session_focus', 'practice')} exercise",
        "mood": f"{assessment_answers.get('mood', 'upbeat')} guitar practice"
    }
    
    # Search for videos for each assessment answer
    for key, query in search_queries.items():
        print(f"🔍 Searching for: {query}")
        videos = search_youtube_videos(query, youtube_client, max_results=videos_per_topic)
        results[key] = videos
    
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
            output += "\n"
    
    return output


def get_video_details(video_id: str, youtube_client) -> Dict:
    """
    Get detailed information about a specific video.
    
    Args:
        video_id: YouTube video ID
        youtube_client: YouTube API client
        
    Returns:
        Dict with detailed video information including duration
    """
    if not youtube_client:
        return {}
    
    try:
        request = youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        
        if response.get("items"):
            item = response["items"][0]
            return {
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": item["contentDetails"]["duration"],
                "views": item["statistics"].get("viewCount", "N/A"),
                "likes": item["statistics"].get("likeCount", "N/A"),
                "description": item["snippet"]["description"]
            }
        return {}
    except HttpError as e:
        print(f"❌ Error fetching video details: {e}")
        return {}
