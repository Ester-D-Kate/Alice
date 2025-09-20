"""
Alice AI Audio Processing with Groq API
Uses Groq's Whisper-large-v3-turbo for transcription and Llama for responses
"""

import logging
import tempfile
import os
from typing import Dict, Any, Optional
from groq import Groq
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

class GroqAudioProcessor:
    def __init__(self):
        """Initialize Groq client"""
        try:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
            logger.info("✅ Groq Audio Processor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            raise

    def transcribe_audio(self, audio_file) -> Dict[str, Any]:
        """
        Transcribe audio using Groq's Whisper-large-v3-turbo
        
        Args:
            audio_file: Uploaded audio file (FastAPI UploadFile)
            
        Returns:
            Dict containing transcription and metadata
        """
        try:
            # Read audio file content
            audio_content = audio_file.file.read()
            audio_file.file.seek(0)  # Reset file pointer
            
            # Determine file extension from content type
            content_type = audio_file.content_type
            if 'webm' in content_type:
                extension = '.webm'
            elif 'mp4' in content_type:
                extension = '.mp4'
            elif 'wav' in content_type:
                extension = '.wav'
            elif 'ogg' in content_type:
                extension = '.ogg'
            else:
                extension = '.webm'  # Default
            
            # Create temporary file for Groq processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe with Groq Whisper-large-v3-turbo
                with open(temp_file_path, "rb") as file:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=file,
                        model="whisper-large-v3-turbo",
                        prompt="This is a voice command for an AI assistant named Alice.",
                        response_format="json",
                        language="en",
                        temperature=0.0
                    )
                
                transcribed_text = transcription.text.strip()
                
                logger.info(f"🎙️ Groq transcription: '{transcribed_text[:100]}...'")
                
                return {
                    "success": True,
                    "transcription": transcribed_text,
                    "language": "en",
                    "model": "whisper-large-v3-turbo",
                    "duration": getattr(transcription, 'duration', 0)
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"❌ Groq audio transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transcription": ""
            }

# Global instance
_groq_audio_processor = None

def get_groq_audio_processor() -> GroqAudioProcessor:
    """Get global Groq audio processor instance"""
    global _groq_audio_processor
    if _groq_audio_processor is None:
        _groq_audio_processor = GroqAudioProcessor()
    return _groq_audio_processor
