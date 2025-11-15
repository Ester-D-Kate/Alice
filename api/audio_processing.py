"""
Audio Processing API - Converts voice to text and triggers chat
Flow: Audio → Whisper → Text → Chat API
"""

import logging
import tempfile
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from groq import Groq
from api.schemas import AudioResponse, ChatRequest
from .chat import process_chat_message
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["Audio Processing"])

# Audio processing config
GROQ_API_KEY_WHISPER = os.getenv("GROQ_API_KEY")  # Use main key for Whisper
groq_client = Groq(api_key=GROQ_API_KEY_WHISPER)

async def track_processing_time():
    start_time = datetime.now()
    yield start_time

@router.post("/process", response_model=AudioResponse)
async def process_voice_command(
    audio_file: UploadFile = File(...),
    user_id: str = "default_user",
    start_time: datetime = Depends(track_processing_time)
) -> AudioResponse:
    """
    Process voice input: Audio → Text → Chat → Task Analysis
    """
    try:
        logger.info(f"Processing audio for user {user_id}")
        
        # Step 1: Transcribe audio with Whisper
        transcription = await transcribe_with_whisper(audio_file)
        
        if not transcription.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        logger.info(f"Transcribed: {transcription[:100]}...")
        
        # Step 2: Send transcribed text to chat API
        chat_request = ChatRequest(
            message=transcription,
            user_id=user_id
        )
        
        chat_response = await process_chat_message(chat_request)
        
        # Step 3: Create audio response
        processing_time = (datetime.now() - start_time).total_seconds()
        
        audio_response = AudioResponse(
            success=True,
            transcription=transcription,
            chat_response=chat_response,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
        logger.info(f"Audio processed in {processing_time:.2f}s")
        return audio_response
        
    except Exception as e:
        logger.error(f"Audio processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Audio processing failed: {str(e)}"
        )

async def transcribe_with_whisper(audio_file: UploadFile) -> str:
    """Transcribe audio file using Groq Whisper"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Transcribe with Groq Whisper
        with open(tmp_path, "rb") as audio:
            transcription = groq_client.audio.transcriptions.create(
                file=audio,
                model="whisper-large-v3",
                language="en"
            )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return transcription.text.strip()
        
    except Exception as e:
        logger.error(f"Whisper transcription failed: {str(e)}")
        raise
