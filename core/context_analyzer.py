import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from .database_manager import get_db_manager
from llm import get_llm_response, extract_json_from_response
from config import INTENT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class AliceContextAnalyzer:
    def __init__(self):
        self.db = get_db_manager()
        
    def analyze_user_intent(self, message: str, user_id: str = None) -> Dict:
        """Comprehensive user intent analysis"""
        
        try:
            # Get conversation history for context
            recent_context = self.db.get_conversation_context(user_id, limit=3) if user_id else []
            
            # Find similar past conversations
            similar_conversations = self.db.find_similar_conversations(message, user_id, limit=2)
            
            # Build context for LLM
            context_text = ""
            if recent_context:
                context_text += f"Recent conversation: {recent_context[0]['message']} -> {recent_context[0]['response'][:100]}\n"
            
            if similar_conversations:
                context_text += f"Similar past: {similar_conversations[0]['message']}\n"
            
            # Prepare analysis prompt
            analysis_prompt = f"""
            {INTENT_ANALYSIS_PROMPT}
            
            User message: "{message}"
            Context: {context_text}
            
            Analyze this message and return ONLY valid JSON with:
            {{
                "intent": "search|computer_control|conversation|template_save|template_use",
                "confidence": 0.85,
                "entities": ["entity1", "entity2"],
                "actions": ["action1", "action2"],
                "requires_search": true,
                "requires_computer": false,
                "search_query": "optimized search query if needed",
                "computer_task": "specific computer task if applicable",
                "template_match": null,
                "priority": "high|medium|low",
                "estimated_complexity": "simple|medium|complex"
            }}
            """
            
            # Get LLM analysis
            llm_result = get_llm_response(
                analysis_prompt,
                system_prompt="You are an expert at analyzing user intent. Return only valid JSON.",
                temperature=0.3
            )
            
            if llm_result["success"]:
                # Extract JSON from response
                analysis = extract_json_from_response(llm_result["response"])
                
                if analysis:
                    # Enhance analysis with our logic
                    analysis = self._enhance_analysis(analysis, message, recent_context)
                    
                    # Store analysis for learning
                    if user_id:
                        self._store_analysis(user_id, message, analysis)
                    
                    logger.info(f"✅ Intent analyzed: {analysis['intent']} (confidence: {analysis['confidence']:.2f})")
                    return analysis
            
        except Exception as e:
            logger.error(f"❌ Intent analysis failed: {e}")
        
        # Fallback analysis using keyword detection
        return self._fallback_analysis(message)
    
    def _enhance_analysis(self, analysis: Dict, message: str, context: List[Dict]) -> Dict:
        """Enhance LLM analysis with rule-based logic"""
        
        try:
            # Enhance search detection
            search_keywords = ["search", "find", "look up", "research", "information about", "what is", "how to", "latest", "news"]
            if any(keyword in message.lower() for keyword in search_keywords):
                analysis["requires_search"] = True
                if not analysis.get("search_query"):
                    analysis["search_query"] = message
            
            # Enhance computer control detection  
            computer_keywords = ["open", "close", "type", "click", "control", "automate", "screenshot", "mouse", "keyboard"]
            if any(keyword in message.lower() for keyword in computer_keywords):
                analysis["requires_computer"] = True
                if not analysis.get("computer_task"):
                    analysis["computer_task"] = message
            
            # Set priority based on keywords
            urgent_keywords = ["urgent", "immediately", "now", "asap", "quickly"]
            if any(keyword in message.lower() for keyword in urgent_keywords):
                analysis["priority"] = "high"
            
            # Estimate complexity
            complex_indicators = ["and then", "after that", "multiple", "several", "complex", "advanced"]
            if any(indicator in message.lower() for indicator in complex_indicators) or len(message) > 100:
                analysis["estimated_complexity"] = "complex"
            elif len(message) < 20:
                analysis["estimated_complexity"] = "simple"
            
            # Add metadata
            analysis["analysis_timestamp"] = datetime.now().isoformat()
            analysis["message_length"] = len(message)
            analysis["has_context"] = len(context) > 0
            
        except Exception as e:
            logger.error(f"Analysis enhancement failed: {e}")
        
        return analysis
    
    def _fallback_analysis(self, message: str) -> Dict:
        """Simple keyword-based fallback analysis"""
        
        message_lower = message.lower()
        
        # Determine intent
        intent = "conversation"  # default
        confidence = 0.5
        
        if any(word in message_lower for word in ["search", "find", "what", "how", "when", "where", "why"]):
            intent = "search"
            confidence = 0.7
        elif any(word in message_lower for word in ["open", "type", "click", "control", "screenshot"]):
            intent = "computer_control"
            confidence = 0.6
        elif any(word in message_lower for word in ["save", "remember", "template", "workflow"]):
            intent = "template_save"
            confidence = 0.6
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": [],
            "actions": [intent],
            "requires_search": intent == "search",
            "requires_computer": intent == "computer_control",
            "search_query": message if intent == "search" else None,
            "computer_task": message if intent == "computer_control" else None,
            "template_match": None,
            "priority": "medium",
            "estimated_complexity": "simple",
            "analysis_timestamp": datetime.now().isoformat(),
            "fallback": True
        }
    
    def _store_analysis(self, user_id: str, message: str, analysis: Dict):
        """Store analysis result for learning"""
        try:
            # Cache analysis for quick access
            cache_key = f"analysis:{user_id}:{hash(message)}"
            self.db.redis_conn.setex(
                cache_key, 
                3600,  # 1 hour
                json.dumps(analysis)
            )
            
        except Exception as e:
            logger.error(f"Analysis storage failed: {e}")
    
    def get_cached_analysis(self, user_id: str, message: str) -> Optional[Dict]:
        """Get cached analysis if available"""
        try:
            cache_key = f"analysis:{user_id}:{hash(message)}"
            cached = self.db.redis_conn.get(cache_key)
            
            if cached:
                return json.loads(cached)
                
        except Exception as e:
            logger.error(f"Analysis cache retrieval failed: {e}")
        
        return None
    
    def analyze_search_needs(self, message: str, intent_analysis: Dict) -> Dict:
        """Determine specific search requirements"""
        
        search_analysis = {
            "needs_search": intent_analysis.get("requires_search", False),
            "search_query": intent_analysis.get("search_query", message),
            "search_type": "general",
            "urgency": intent_analysis.get("priority", "medium")
        }
        
        # Determine search type
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["news", "latest", "recent", "today", "current"]):
            search_analysis["search_type"] = "news"
        elif any(word in message_lower for word in ["how to", "tutorial", "guide", "steps"]):
            search_analysis["search_type"] = "tutorial"
        elif any(word in message_lower for word in ["definition", "what is", "meaning", "explain"]):
            search_analysis["search_type"] = "definition"
        
        return search_analysis

# Global instance
_context_analyzer = None

def get_context_analyzer() -> AliceContextAnalyzer:
    """Get global context analyzer instance"""
    global _context_analyzer
    if _context_analyzer is None:
        _context_analyzer = AliceContextAnalyzer()
    return _context_analyzer
