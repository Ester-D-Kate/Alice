"""
Main Chat API - Handles all text input and triggers task analysis
This is the MAIN endpoint that everything flows through
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from utils.core.context_analyzer import get_task_analyzer
from api.schemas import ChatRequest, ChatResponse, TaskAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/message", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """
    MAIN CHAT ENDPOINT - All text input comes here
    Flow: Text → Task Analysis → Search (if needed) → Final Response
    """
    try:
        logger.info(f"Chat request from {request.user_id}: {request.message[:50]}...")
        
        # Step 1: Analyze the task using our first LLM
        analyzer = get_task_analyzer()
        task_analysis = await analyzer.analyze_task(request.message, request.user_id)
        
        # Step 2: Process based on analysis results
        if task_analysis["can_answer_directly"] == 1:
            # Alice can answer directly
            response_text = task_analysis["direct_response"]
            completed = True
            next_action = None
            
        elif task_analysis["requires_search"] == 1:
            # Execute search automatically
            logger.info("Search required - executing web search...")
            response_text = task_analysis["user_feedback"]  # "Let me search for that..."
            completed = False
            next_action = "search_agent"
            
            # Note: The actual search execution should be done by the frontend
            # calling /api/v1/search/answer endpoint, or we can execute it here
            # For now, we'll let the frontend handle it
            
        else:
            # Other requirements (database, computer control, etc.)
            response_text = task_analysis["user_feedback"]
            completed = False
            
            # Determine next action
            if task_analysis["requires_database"] == 1:
                next_action = "database_agent"
            elif task_analysis["requires_computer"] == 1:
                next_action = "computer_agent"
            else:
                next_action = "conversation_agent"
        
        # Step 3: Create response
        chat_response = ChatResponse(
            success=True,
            message=response_text,
            task_analysis=TaskAnalysisResponse(**task_analysis),
            task_completed=completed,
            next_action=next_action,
            user_id=request.user_id,
            timestamp=datetime.now()
        )
        
        logger.info(f"Chat processed: {task_analysis['task_type']} -> {next_action or 'completed'}")
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )

@router.get("/health")
async def chat_health():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "service": "Chat API",
        "timestamp": datetime.now().isoformat()
    }
