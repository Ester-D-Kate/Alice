"""
Alice Task Analyzer - Simple API Models
Only the models we need for chat.py and audio_processing.py
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Task Analysis Response (what the first LLM returns)
class TaskAnalysisResponse(BaseModel):
    task_type: Literal["simple_question", "search_required", "database_required", "computer_control"]
    requires_search: int = Field(..., description="1 if needs search, 0 if not")
    requires_database: int = Field(..., description="1 if needs database, 0 if not")
    requires_computer: int = Field(..., description="1 if needs computer control, 0 if not")
    can_answer_directly: int = Field(..., description="1 if can answer now, 0 if needs processing")
    direct_response: Optional[str] = Field(None, description="Direct answer if available")
    user_feedback: str = Field(..., description="What Alice tells user")
    process_needed: str = Field(..., description="What Alice needs to do")
    confidence: float = Field(..., description="Analysis confidence 0.0-1.0")

# Chat Models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's text message")
    user_id: str = Field(default="default_user", description="User ID")

class ChatResponse(BaseModel):
    success: bool = Field(..., description="Request success")
    message: str = Field(..., description="Alice's response")
    task_analysis: TaskAnalysisResponse = Field(..., description="Analysis from first LLM")
    task_completed: bool = Field(..., description="Whether task is done")
    next_action: Optional[str] = Field(None, description="Next agent to call")
    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(default_factory=datetime.now)

# Audio Models
class AudioResponse(BaseModel):
    success: bool = Field(..., description="Processing success")
    transcription: str = Field(..., description="Transcribed text from audio")
    chat_response: ChatResponse = Field(..., description="Chat processing results")
    processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
