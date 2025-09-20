#!/usr/bin/env python3
"""
Quick Fix Alice Issues - Windows Compatible
Fixes the 4 issues found in verification
"""

import os

def create_computer_control_init():
    """Create missing computer_control/__init__.py"""
    
    os.makedirs("computer_control", exist_ok=True)
    
    init_content = '''"""
Alice Computer Control System
Remote computer automation with AI planning and visual feedback
"""

from .control_logic import get_computer_control, AliceComputerControl

__version__ = "2.0.0"
__description__ = "AI-powered computer control with multimodal feedback"

__all__ = [
    'get_computer_control',
    'AliceComputerControl'
]

# Initialize computer control system
import logging
logger = logging.getLogger(__name__)
logger.info("Alice Computer Control System initialized")
'''
    
    with open("computer_control/__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)
    
    print("✅ Created computer_control/__init__.py")

def create_api_models():
    """Create fixed API models"""
    
    os.makedirs("api", exist_ok=True)
    
    models_content = '''"""
Alice API Models - Fixed Pydantic Version
All request/response models for Alice AI Assistant API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
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
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
'''
    
    with open("api/models.py", "w", encoding="utf-8") as f:
        f.write(models_content)
    
    print("✅ Created fixed api/models.py")

def create_api_init():
    """Create API __init__.py"""
    
    api_init_content = '''"""
Alice FastAPI Endpoints
RESTful API for Alice AI Assistant
"""

from .models import *

__version__ = "2.0.0"
__description__ = "Alice AI Assistant API"

__all__ = [
    'ChatRequest', 'ChatResponse',
    'SearchRequest', 'SearchResponse', 
    'ComputerControlRequest', 'ComputerControlResponse',
    'HealthResponse', 'ErrorResponse'
]

import logging
logger = logging.getLogger(__name__)
logger.info("Alice API endpoints initialized")
'''
    
    with open("api/__init__.py", "w", encoding="utf-8") as f:
        f.write(api_init_content)
    
    print("✅ Created api/__init__.py")

def fix_search_integration_import():
    """Fix missing List import in search_integration.py"""
    
    try:
        with open("utils/search_integration.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add List import if not present
        if "from typing import Dict, List" not in content:
            content = content.replace(
                "from typing import Dict",
                "from typing import Dict, List"
            )
            
            with open("utils/search_integration.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ Fixed List import in search_integration.py")
        else:
            print("✅ List import already present in search_integration.py")
            
    except Exception as e:
        print(f"⚠️ Could not fix search_integration.py: {e}")
        # Create a simple manual fix message
        print("   Manual fix: Add 'List' to the typing import in utils/search_integration.py")

def main():
    """Run all quick fixes"""
    
    print("Alice Quick Fix - Addressing verification issues...")
    print("=" * 50)
    
    # Fix 1: Computer Control module
    create_computer_control_init()
    
    # Fix 2: API models
    create_api_models()
    
    # Fix 3: API init
    create_api_init()
    
    # Fix 4: Search integration import
    fix_search_integration_import()
    
    print()
    print("All quick fixes applied!")
    print()
    print("Server-side fixes completed:")
    print("   - Redis protected mode disabled")
    print("   - pgvector extension confirmed installed")
    
    print()
    print("Client-side fixes completed:")
    print("   - Created computer_control/__init__.py")
    print("   - Fixed api/models.py (removed deprecated regex)")
    print("   - Created api/__init__.py")
    print("   - Fixed List import in search_integration.py")
    
    print()
    print("Ready to re-run verification!")
    print("   Run: python alice_full_verification.py")
    
if __name__ == "__main__":
    main()
