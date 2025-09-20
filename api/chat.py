import logging
import asyncio
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from .models import ChatRequest, ChatResponse, MultimodalRequest, MultimodalResponse
from core.context_analyzer import get_context_analyzer
from core.database_manager import get_db_manager
from computer_control.control_logic import get_computer_control
from llm import get_llm_response, get_multimodal_response, get_model_info
from utils.search_integration import alice_search
from config import ALICE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Dependency for tracking request time
async def track_processing_time():
    start_time = datetime.now()
    yield start_time

@router.post("/", response_model=ChatResponse)
async def chat_with_alice(
    request: ChatRequest,
    start_time: datetime = Depends(track_processing_time)
):
    """
    🧠 Main chat endpoint - Alice's brain powered by Llama 4 Maverick
    Handles conversation, search, and computer control
    """
    
    try:
        logger.info(f"💬 Chat request from user: {request.user_id}")
        
        # Initialize components
        context_analyzer = get_context_analyzer()
        computer_control = get_computer_control()
        db = get_db_manager()
        
        # Step 1: Analyze user intent with advanced reasoning
        intent_analysis = context_analyzer.analyze_user_intent(
            request.message, 
            request.user_id
        )
        
        logger.info(f"🎯 Intent analyzed: {intent_analysis['intent']} (confidence: {intent_analysis['confidence']:.2f})")
        
        # Step 2: Handle based on intent
        search_results = None
        computer_execution = None
        template_used = None
        
        # Search handling
        if intent_analysis.get("requires_search", False) or request.use_search:
            logger.info("🔍 Performing web search")
            search_query = intent_analysis.get("search_query", request.message)
            search_response = await alice_search(search_query)
            
            if search_response["success"]:
                search_results = search_response["results"]
                logger.info(f"✅ Found {len(search_results)} search results")
            else:
                logger.warning(f"⚠️ Search failed: {search_response.get('error', 'Unknown error')}")
        
        # Computer control handling
        if intent_analysis.get("requires_computer", False) or request.use_computer_control:
            if request.device_id:
                logger.info(f"🖥️ Executing computer control on {request.device_id}")
                computer_task = intent_analysis.get("computer_task", request.message)
                
                execution_result = await computer_control.execute_computer_task(
                    computer_task,
                    request.device_id,
                    request.user_id
                )
                
                computer_execution = execution_result
                template_used = execution_result.get("template_used")
                
                logger.info(f"✅ Computer control {'succeeded' if execution_result['success'] else 'failed'}")
            else:
                logger.warning("⚠️ Computer control requested but no device_id provided")
        
        # Step 3: Generate Alice's response using Llama 4 Maverick
        alice_prompt = request.message
        
        # Add context from search results
        if search_results:
            search_context = "\n".join([
                f"🔍 Search Result {i+1}: {result.get('title', 'No title')} - {result.get('snippet', 'No description')[:200]}"
                for i, result in enumerate(search_results[:3])
            ])
            alice_prompt = f"""User question: {request.message}

🌐 Web Search Results:
{search_context}

Please provide a comprehensive answer using this information. Be conversational and helpful."""
        
        # Add context from computer execution
        if computer_execution:
            execution_summary = f"""
🖥️ Computer Control Executed:
- Task: {computer_execution.get('task_description', 'Unknown')}
- Device: {request.device_id}
- Success: {computer_execution.get('success', False)}
- Steps completed: {computer_execution.get('steps_completed', 0)}/{computer_execution.get('total_steps', 0)}
"""
            if computer_execution.get('success'):
                execution_summary += f"- Execution time: {computer_execution.get('execution_time', 0):.1f}s"
            else:
                execution_summary += f"- Errors: {', '.join(computer_execution.get('errors', []))}"
            
            alice_prompt = f"""User request: {request.message}

{execution_summary}

Please explain what was accomplished and provide any relevant follow-up suggestions."""
        
        # Get Alice's response with appropriate task type
        task_type = "conversation"
        if search_results:
            task_type = "analysis"
        elif computer_execution:
            task_type = "reasoning"
        
        llm_result = get_llm_response(
            alice_prompt,
            system_prompt=ALICE_SYSTEM_PROMPT,
            task_type=task_type,
            temperature=request.temperature
        )
        
        if not llm_result["success"]:
            raise HTTPException(status_code=500, detail=f"LLM processing failed: {llm_result.get('error', 'Unknown error')}")
        
        alice_response = llm_result["response"]
        
        # Step 4: Store conversation for learning
        if request.user_id:
            try:
                db.store_conversation(
                    user_id=request.user_id,
                    user_message=request.message,
                    alice_response=alice_response,
                    intent=intent_analysis["intent"],
                    confidence=intent_analysis["confidence"],
                    context_data={
                        "search_performed": bool(search_results),
                        "computer_control_used": bool(computer_execution),
                        "template_used": template_used,
                        "model_info": llm_result.get("performance", {})
                    }
                )
            except Exception as e:
                logger.error(f"❌ Conversation storage failed: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            success=True,
            response=alice_response,
            intent_analysis=intent_analysis,
            search_results=search_results,
            computer_execution=computer_execution,
            template_used=template_used,
            model_info=llm_result.get("performance", get_model_info()),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Alice encountered an error: {str(e)}"
        )

@router.post("/multimodal", response_model=MultimodalResponse)
async def multimodal_chat(
    request: MultimodalRequest,
    start_time: datetime = Depends(track_processing_time)
):
    """
    🖼️ Multimodal chat endpoint - Text + Image processing with Llama 4 Maverick
    """
    
    try:
        logger.info(f"🖼️ Multimodal request: {'with image' if request.image_data else 'text only'}")
        
        # Use Llama 4 Maverick's multimodal capabilities
        if request.image_data:
            multimodal_result = get_multimodal_response(
                request.text_prompt,
                image_data=request.image_data,
                system_prompt="You are Alice with advanced multimodal capabilities. Analyze images and provide detailed, helpful responses."
            )
        else:
            # Fallback to text-only processing
            multimodal_result = get_llm_response(
                request.text_prompt,
                task_type=request.task_type,
                system_prompt="You are Alice using Llama 4 Maverick's advanced reasoning capabilities."
            )
        
        if not multimodal_result["success"]:
            raise HTTPException(status_code=500, detail=f"Multimodal processing failed: {multimodal_result.get('error', 'Unknown error')}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return MultimodalResponse(
            success=True,
            text_prompt=request.text_prompt,
            response=multimodal_result["response"],
            image_analyzed=bool(request.image_data),
            model_capabilities=get_model_info()["capabilities"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multimodal processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal processing error: {str(e)}"
        )

@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 10):
    """Get recent chat history for user"""
    
    try:
        db = get_db_manager()
        history = db.get_conversation_context(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"❌ History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Clear chat history for user"""
    
    try:
        db = get_db_manager()
        
        # Clear from cache
        cache_key = f"recent_conversations:{user_id}"
        db.redis_conn.delete(cache_key)
        
        # Note: We don't delete from PostgreSQL for data integrity
        # but we could implement a "soft delete" feature here
        
        return {
            "success": True,
            "message": f"Chat history cleared for user {user_id}",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ History clearing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
