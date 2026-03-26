"""Pydantic models for API request/response validation."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AssessmentAnswer(BaseModel):
    """Request body for assessment submission."""
    guitar_type: str
    skill_level: str
    genre: str
    session_focus: str
    mood: str


class SessionState(BaseModel):
    """Current session state."""
    session_id: str
    phase: str  # 'assessment', 'plan', 'refinement'
    assessment_answers: Optional[Dict[str, str]] = None
    generated_plan: Optional[str] = None
    conversation_history: List[Dict[str, str]] = []


class Practiceplan(BaseModel):
    """Generated practice plan response."""
    plan: str
    session_id: str


class ChatMessage(BaseModel):
    """Chat message for refinement phase."""
    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Response from refinement chat."""
    response: str
    updated_plan: Optional[str] = None
