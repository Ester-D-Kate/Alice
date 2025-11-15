"""
Alice's Task Analyzer Agent - First LLM
"""
import logging
import json
from groq import Groq
from .config import API_KEY, MODEL, TEMPERATURE, MAX_TOKENS, SYSTEM_PROMPT, FALLBACK_RESPONSE

logger = logging.getLogger(__name__)

class AliceTaskAnalyzer:
    def __init__(self):
        self.groq_client = Groq(api_key=API_KEY)
        
        # Empty context variables for now
        self.previous_context = ""
        self.common_mistakes = ""
        self.user_patterns = ""
    
    async def analyze_task(self, user_query: str, user_id: str) -> dict:
        """Analyze what user wants Alice to do"""
        try:
            # Build prompt
            prompt = SYSTEM_PROMPT.format(
                previous_context=self.previous_context,
                common_mistakes=self.common_mistakes,
                user_patterns=self.user_patterns
            )
            
            full_prompt = f"{prompt}\n\nUSER QUERY: \"{user_query}\"\n\nAnalyze and respond with JSON:"
            
            # Call Groq
            response = self.groq_client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Task analyzed: {analysis.get('task_type')} for: {user_query[:30]}...")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return FALLBACK_RESPONSE

# Global instance
_analyzer = None

def get_task_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = AliceTaskAnalyzer()
    return _analyzer
