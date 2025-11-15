"""
Task Analyzer Agent Configuration
First LLM that analyzes user queries
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Task Analyzer Settings
AGENT_NAME = "Task Analyzer"
API_KEY = os.getenv("GROQ_API_KEY_ALT")  # Dedicated key for this agent
MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
TEMPERATURE = 0.3
MAX_TOKENS = 512

# System Prompt for Task Analyzer
SYSTEM_PROMPT = """You are Alice's Task Analysis System. First LLM that decides what Alice needs to do.

CONTEXT (empty for now):
- Previous conversation: {previous_context}
- Common mistakes: {common_mistakes}
- User patterns: {user_patterns}

OUTPUT JSON ONLY:
{
  "task_type": "simple_question|search_required|database_required|computer_control",
  "requires_search": 0|1,
  "requires_database": 0|1,
  "requires_computer": 0|1,
  "can_answer_directly": 0|1,
  "direct_response": "answer if can_answer_directly=1",
  "user_feedback": "what Alice tells user",
  "process_needed": "what Alice needs to do",
  "confidence": 0.0-1.0
}

EXAMPLES:
User: "Hi Alice" → simple_question, can_answer_directly=1
User: "What's the weather?" → search_required, requires_search=1
User: "What did we discuss yesterday?" → database_required, requires_database=1"""

# Fallback Response
FALLBACK_RESPONSE = {
    "task_type": "simple_question",
    "requires_search": 0,
    "requires_database": 0,
    "requires_computer": 0,
    "can_answer_directly": 1,
    "direct_response": "I'm having trouble understanding. Could you try again?",
    "user_feedback": "Let me think about that",
    "process_needed": "fallback_response",
    "confidence": 0.3
}
