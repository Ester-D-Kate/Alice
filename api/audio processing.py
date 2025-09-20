"""
🎙️ Alice AI Audio Processing API - Conversation + Computer Control Only
Handles voice commands with Groq Whisper + Alice AI integration
"""

import logging
import tempfile
import os
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from groq import Groq

from .models import AudioProcessingResponse
from core.context_analyzer import get_context_analyzer
from core.database_manager import get_db_manager
from llm import get_llm_response, get_model_info
from config import GROQ_API_KEY, ALICE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["Audio Processing"])

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Dependency for tracking request time
async def track_processing_time():
    start_time = datetime.now()
    yield start_time

async def transcribe_audio_with_groq(audio_file: UploadFile) -> Dict[str, Any]:
    """Transcribe audio using Groq's Whisper-large-v3-turbo"""
    try:
        # Read audio file content
        audio_content = await audio_file.read()
        await audio_file.seek(0)
        
        # Determine file extension
        content_type = audio_file.content_type or ""
        if 'webm' in content_type:
            extension = '.webm'
        elif 'mp4' in content_type:
            extension = '.mp4'
        elif 'wav' in content_type:
            extension = '.wav'
        else:
            extension = '.webm'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe with Groq Whisper
            with open(temp_file_path, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(audio_file.filename, file, audio_file.content_type),
                    model="whisper-large-v3-turbo",
                    prompt="This is a voice command for Alice AI assistant.",
                    response_format="json",
                    language="en",
                    temperature=0.0
                )
            
            transcribed_text = transcription.text.strip()
            logger.info(f"🎙️ Transcribed: '{transcribed_text[:100]}...'")
            
            return {
                "success": True,
                "transcription": transcribed_text,
                "model": "whisper-large-v3-turbo"
            }
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"❌ Groq transcription failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "transcription": ""
        }

async def generate_ducky_script_for_voice(text: str) -> str:
    """Generate computer control script from voice command using Groq"""
    try:
        prompt = f"""Convert this voice command to a Windows ducky script:

Voice Command: "{text}"

Examples:
- "take a screenshot" → GUI r\nDELAY 500\ncmd\nENTER\nDELAY 1000\nsnippingtool\nENTER
- "open calculator" → GUI r\nDELAY 500\ncalc\nENTER  
- "open notepad" → GUI r\nDELAY 500\nnotepad\nENTER
- "open chrome" → GUI r\nDELAY 500\nchrome\nENTER

Return ONLY the script, no explanations:"""

        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=150,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Ducky script generation failed: {e}")
        return ""

@router.post("/process_audio", response_model=AudioProcessingResponse)
async def process_audio(
    audio_file: UploadFile = File(...),
    user_id: str = "web_audio_user",
    start_time: datetime = Depends(track_processing_time)
):
    """
    🎙️ Process audio file with Alice AI - Conversation + Computer Control Only
    
    Workflow:
    1. Transcribe audio with Groq Whisper-large-v3-turbo
    2. Analyze intent with Alice's context analyzer  
    3. Generate ducky script if computer control needed
    4. Generate Alice's conversational response with Llama 4 Maverick
    5. Return structured response for web interface
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        logger.info(f"🎙️ Processing audio from user: {user_id}")
        
        # Step 1: Transcribe audio with Groq Whisper
        transcription_result = await transcribe_audio_with_groq(audio_file)
        
        if not transcription_result["success"]:
            return AudioProcessingResponse(
                success=False,
                output_natural_response=f"Sorry, I couldn't process the audio: {transcription_result['error']}",
                output_ducky_script="",
                output_appliances_response={},  # Always empty dict
                transcription="",
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error": transcription_result['error']}
            )
        
        transcribed_text = transcription_result["transcription"]
        
        if not transcribed_text.strip():
            return AudioProcessingResponse(
                success=True,
                output_natural_response="I couldn't hear anything clearly. Please try speaking again.",
                output_ducky_script="",
                output_appliances_response={},  # Always empty dict
                transcription="",
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={"issue": "empty_transcription"}
            )
        
        logger.info(f"📝 Transcribed: '{transcribed_text}'")
        
        # Step 2: Initialize Alice components
        context_analyzer = get_context_analyzer()
        db = get_db_manager()
        
        # Step 3: Analyze user intent
        intent_analysis = context_analyzer.analyze_user_intent(
            transcribed_text,
            user_id
        )
        
        logger.info(f"🎯 Intent: {intent_analysis['intent']} (confidence: {intent_analysis['confidence']:.2f})")
        
        # Step 4: Check for computer control commands and generate ducky script
        computer_keywords = ["screenshot", "open", "click", "type", "press", "start", "run", "execute", "launch", "minimize", "close"]
        needs_computer_control = any(keyword in transcribed_text.lower() for keyword in computer_keywords)
        
        ducky_script = ""
        if needs_computer_control:
            ducky_script = await generate_ducky_script_for_voice(transcribed_text)
            logger.info(f"🖥️ Generated ducky script: {ducky_script[:50]}...")
        
        # Step 5: Generate Alice's conversational response
        if ducky_script:
            alice_prompt = f"""User voice command: "{transcribed_text}"

I've generated a computer control script to execute this command. Please provide a friendly, conversational response acknowledging what I'm about to do for them. Be natural and helpful since this is a voice interaction.

Keep it brief and conversational - something like "I'll help you [action] right away!" or "Let me [action] for you!"

Response:"""
        else:
            alice_prompt = f"""User voice command: "{transcribed_text}"

This seems like a conversational request. Please provide a helpful, natural response. Since this is a voice interaction, be friendly and conversational.

Response:"""
        
        llm_result = get_llm_response(
            alice_prompt,
            system_prompt=ALICE_SYSTEM_PROMPT,
            task_type="conversation",
            temperature=0.7
        )
        
        if not llm_result["success"]:
            alice_response = "I understand your request! Let me help you with that." if ducky_script else "I'm here to help! What can I do for you?"
        else:
            alice_response = llm_result["response"]
        
        # Step 6: Store conversation in database
        conversation_id = None
        try:
            conversation_id = db.store_conversation(
                user_id=user_id,
                user_message=transcribed_text,
                alice_response=alice_response,
                intent=intent_analysis["intent"],
                confidence=intent_analysis["confidence"],
                context_data={
                    "source": "audio_web_interface",
                    "transcription_model": "whisper-large-v3-turbo",
                    "has_ducky_script": bool(ducky_script),
                    "computer_control": needs_computer_control
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store conversation: {e}")
        
        # Step 7: Return response for web interface
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AudioProcessingResponse(
            success=True,
            output_natural_response=alice_response,
            output_ducky_script=ducky_script,
            output_appliances_response={},  # Always empty dict - not used
            transcription=transcribed_text,
            conversation_id=conversation_id,
            metadata={
                "transcription_model": "whisper-large-v3-turbo",
                "llm_model": "llama-4-maverick",
                "intent": intent_analysis["intent"],
                "confidence": intent_analysis["confidence"],
                "computer_control_detected": needs_computer_control
            },
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Audio processing failed: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        return AudioProcessingResponse(
            success=False,
            output_natural_response=f"I encountered an error processing your voice command: {str(e)}",
            output_ducky_script="",
            output_appliances_response={},  # Always empty dict
            transcription="",
            processing_time=processing_time,
            metadata={"error": str(e)}
        )

@router.get("/health")
async def audio_health_check():
    """Health check for audio processing service"""
    try:
        model_info = get_model_info()
        return {
            "success": True,
            "service": "Alice Audio Processing",
            "whisper_model": "whisper-large-v3-turbo", 
            "llm_model": model_info.get("model", "llama-4-maverick"),
            "capabilities": [
                "audio_transcription",
                "voice_commands", 
                "computer_control_scripts",
                "conversation"
            ],
            "status": "operational"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "Alice Audio Processing",
            "error": str(e),
            "status": "error"
        }
