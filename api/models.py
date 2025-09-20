"""
Alice API Models - Complete Version
All request/response models for Alice AI Assistant API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Chat Models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to Alice")
    user_id: str = Field(..., description="Unique user identifier")
    use_search: bool = Field(default=False, description="Enable web search")
    use_computer_control: bool = Field(default=False, description="Enable computer control")
    use_template: bool = Field(default=True, description="Use existing templates")
    context_limit: int = Field(default=5, description="Number of context messages to include")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")

class ChatResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    response: str = Field(..., description="Alice's response")
    intent: Optional[str] = Field(None, description="Detected user intent")
    confidence: Optional[float] = Field(None, description="Intent confidence score")
    template_used: Optional[Dict] = Field(None, description="Template information if used")
    search_results: Optional[List[Dict]] = Field(None, description="Search results if search was used")
    execution_result: Optional[Dict] = Field(None, description="Computer control result if used")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for tracking")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

# Search Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=2, ge=1, le=10, description="Maximum number of results")
    user_id: Optional[str] = Field(None, description="User ID for personalization")

class SearchResponse(BaseModel):
    success: bool = Field(..., description="Search success status")
    query: str = Field(..., description="Original search query")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")
    processing_time: float = Field(..., description="Search processing time")
    search_engine: str = Field(default="DuckDuckGo", description="Search engine used")

# Computer Control Models
class ComputerControlRequest(BaseModel):
    task_description: str = Field(..., description="Description of task to perform")
    device_id: str = Field(..., description="Target device ID")
    user_id: str = Field(..., description="User requesting the task")
    use_template: bool = Field(default=True, description="Use existing templates")
    require_confirmation: bool = Field(default=False, description="Require user confirmation")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Task timeout")

class ComputerControlResponse(BaseModel):
    success: bool = Field(..., description="Task execution success")
    task_id: str = Field(..., description="Unique task identifier")
    device_id: str = Field(..., description="Target device ID")
    execution_plan: Optional[Dict] = Field(None, description="Generated execution plan")
    execution_result: Dict = Field(..., description="Execution results")
    screenshots: List[Dict] = Field(default_factory=list, description="Screenshots taken during execution")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Total execution time")

# Screenshot Models
class ScreenshotRequest(BaseModel):
    device_id: str = Field(..., description="Device to capture screenshot from")
    quality: str = Field(default="high", description="Screenshot quality")
    analyze: bool = Field(default=False, description="Perform AI analysis")

class ScreenshotResponse(BaseModel):
    success: bool = Field(..., description="Screenshot success status")
    device_id: str = Field(..., description="Source device ID")
    image_data: Optional[str] = Field(None, description="Base64 encoded image")
    analysis: Optional[Dict] = Field(None, description="AI analysis results")
    timestamp: str = Field(..., description="Screenshot timestamp")

# Template Models
class TemplateRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID for personalized templates")
    category: Optional[str] = Field(None, description="Template category filter")
    difficulty: Optional[str] = Field(None, description="Template difficulty filter")

class TemplateResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    templates: List[Dict] = Field(..., description="Available templates")
    total_count: int = Field(..., description="Total templates returned")
    processing_time: float = Field(..., description="Processing time in seconds")

# Device Status Models
class DeviceStatusRequest(BaseModel):
    device_id: str = Field(..., description="Device ID to check status")
    detailed: bool = Field(default=False, description="Include detailed hardware info")

class DeviceStatusResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    device_id: str = Field(..., description="Device ID")
    status: str = Field(..., description="Device status (online/offline/busy)")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")
    hardware_info: Optional[Dict] = Field(None, description="Hardware information")

# Multimodal Models
class MultimodalRequest(BaseModel):
    text_prompt: str = Field(..., description="Text prompt for Alice")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    task_type: str = Field(default="analysis", description="Type of multimodal task")
    user_id: str = Field(..., description="User ID")

class MultimodalResponse(BaseModel):
    success: bool = Field(..., description="Request success status")
    response: str = Field(..., description="Alice's multimodal response")
    analysis_type: str = Field(..., description="Type of analysis performed")
    confidence: float = Field(..., description="Analysis confidence score")
    processing_time: float = Field(..., description="Processing time in seconds")

# Health Models
class HealthResponse(BaseModel):
    success: bool = Field(default=True, description="System health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    model: Optional[str] = Field(None, description="LLM model information")
    capabilities: List[str] = Field(default_factory=list, description="Available capabilities")
    uptime: float = Field(..., description="Service uptime in seconds")

# Error Models
class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")
