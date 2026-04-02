"""FastAPI server for AI Guitar Coach application."""

import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.models import AssessmentAnswer, Practiceplan, ChatMessage, ChatResponse
from api.coaches import (
    initialize_agents_and_vector_store,
    generate_practice_plan,
    refine_plan,
    reset_session,
    get_youtube_recommendations
)


# Global components storage
components = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup."""
    global components
    try:
        components = await initialize_agents_and_vector_store()
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        raise
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Guitar Coach API",
    description="AI-powered guitar practice coaching API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Guitar Coach API is running"}


@app.post("/api/initialize")
async def initialize_session():
    """Initialize a new session."""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "phase": "assessment",
        "message": "Session initialized. Please provide assessment answers."
    }


@app.post("/api/assess")
async def process_assessment(assessment: AssessmentAnswer):
    """
    Process assessment answers and generate a practice plan.
    
    Args:
        assessment: AssessmentAnswer with all 5 question responses
        
    Returns:
        Generated practice plan
    """
    if components is None:
        raise HTTPException(status_code=500, detail="Components not initialized")
    
    session_id = str(uuid.uuid4())
    
    try:
        # Convert assessment to dict
        assessment_dict = {
            "guitar_type": assessment.guitar_type,
            "skill_level": assessment.skill_level,
            "genre": assessment.genre,
            "session_focus": assessment.session_focus,
            "mood": assessment.mood
        }
        
        # Generate practice plan
        plan = await generate_practice_plan(assessment_dict, session_id, components)
        
        return {
            "session_id": session_id,
            "phase": "plan",
            "plan": plan
        }
    except Exception as e:
        print(f"Error processing assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refine")
async def process_refinement(chat_message: ChatMessage):
    """
    Process a refinement request to modify the practice plan.
    
    Args:
        chat_message: ChatMessage with user's refinement request and session_id
        
    Returns:
        Refined plan
    """
    if components is None:
        raise HTTPException(status_code=500, detail="Components not initialized")
    
    try:
        result = await refine_plan(
            message=chat_message.message,
            session_id=chat_message.session_id,
            components=components
        )
        
        return {
            "session_id": chat_message.session_id,
            "phase": "refinement",
            "response": result["response"]
        }
    except Exception as e:
        print(f"Error processing refinement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube-recommendations")
async def get_video_recommendations(assessment: AssessmentAnswer):
    """
    Get YouTube video recommendations based on assessment answers.
    
    Args:
        assessment: AssessmentAnswer with all 5 question responses
            - guitar_type: Type of guitar (acoustic, electric, etc.)
            - skill_level: Skill level (beginner, intermediate, advanced)
            - genre: Music genre (rock, blues, jazz, etc.)
            - session_focus: What to focus on (scales, chords, finger dexterity, etc.)
            - mood: Practice mood (energetic, relaxed, focused, etc.)
        
    Returns:
        Dict with YouTube video links grouped by assessment category
    """
    try:
        # Convert assessment to dict
        assessment_dict = {
            "guitar_type": assessment.guitar_type,
            "skill_level": assessment.skill_level,
            "genre": assessment.genre,
            "session_focus": assessment.session_focus,
            "mood": assessment.mood
        }
        
        # Get YouTube recommendations
        result = get_youtube_recommendations(assessment_dict)
        
        return {
            "success": result["success"],
            "videos": result["videos"],
            "raw_results": result.get("raw_results", {})
        }
    except Exception as e:
        print(f"Error getting YouTube recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/reset")
async def reset_session_endpoint(session_id: str):
    """
    Reset a session (clear assessment and plan).
    
    Args:
        session_id: Session ID to reset
        
    Returns:
        Confirmation message
    """
    if reset_session(session_id):
        return {
            "session_id": session_id,
            "message": "Session reset successfully",
            "phase": "assessment"
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
