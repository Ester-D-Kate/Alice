import logging
from typing import Dict, Optional, List, Union
from groq import Groq
from config import (
    GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    REASONING_TEMPERATURE, CREATIVE_TEMPERATURE, CONTEXT_WINDOW_SIZE
)

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

def get_llm_response(
    prompt: str, 
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    task_type: str = "general"
) -> Dict:
    """
    Enhanced LLM response using Llama 4 Maverick's advanced capabilities
    
    Args:
        prompt: User input
        system_prompt: Custom system prompt
        temperature: Custom temperature (auto-selected based on task_type if None)
        max_tokens: Custom token limit
        task_type: "reasoning", "creative", "general", "analysis"
    """
    
    try:
        # Auto-select temperature based on task type
        if temperature is None:
            if task_type in ["reasoning", "analysis", "intent", "planning"]:
                temp = REASONING_TEMPERATURE  # 0.3 - More focused
            elif task_type in ["creative", "conversation", "writing"]:
                temp = CREATIVE_TEMPERATURE   # 0.8 - More creative
            else:
                temp = LLM_TEMPERATURE        # 0.7 - Balanced
        else:
            temp = temperature
        
        # Smart token allocation
        tokens = max_tokens or min(LLM_MAX_TOKENS, len(prompt) * 2 + 1000)
        
        # Enhanced system prompt for Llama 4 Maverick
        if not system_prompt:
            system_prompt = """You are Alice, powered by Llama 4 Maverick's advanced reasoning capabilities. 
            Leverage your 128K context window and multimodal understanding to provide exceptional responses.
            Think step-by-step and use your superior reasoning abilities."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        logger.info(f"🧠 Llama 4 Maverick processing: {task_type} task (temp: {temp:.1f})")
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
            stream=False
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        logger.info(f"✅ Response generated: {usage.completion_tokens} tokens")
        
        return {
            "success": True,
            "response": content,
            "model": LLM_MODEL,
            "task_type": task_type,
            "temperature": temp,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "context_utilization": (usage.prompt_tokens / CONTEXT_WINDOW_SIZE) * 100
            },
            "performance": {
                "model": "llama-4-maverick-17b",
                "context_window": CONTEXT_WINDOW_SIZE,
                "multimodal": True,
                "fast_inference": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Llama 4 Maverick error: {e}")
        return {
            "success": False,
            "response": f"I encountered an error with my advanced reasoning: {str(e)}. Let me try again with a different approach.",
            "error": str(e),
            "model": LLM_MODEL
        }

def get_multimodal_response(
    prompt: str,
    image_data: Optional[str] = None,  # Base64 image data
    system_prompt: Optional[str] = None
) -> Dict:
    """
    Multimodal response using Llama 4 Maverick's native image understanding
    """
    
    try:
        messages = [
            {
                "role": "system", 
                "content": system_prompt or "You are Alice with native multimodal capabilities. Analyze images and text together."
            }
        ]
        
        # Prepare user message with image if provided
        user_message = {"role": "user", "content": prompt}
        
        if image_data:
            # Llama 4 Maverick supports native image understanding
            user_message["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        
        messages.append(user_message)
        
        logger.info("🖼️ Llama 4 Maverick processing multimodal input")
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=REASONING_TEMPERATURE,  # Use reasoning temp for image analysis
            max_tokens=LLM_MAX_TOKENS
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": LLM_MODEL,
            "multimodal": True,
            "usage": response.usage.__dict__
        }
        
    except Exception as e:
        logger.error(f"❌ Multimodal processing failed: {e}")
        return {
            "success": False,
            "response": f"I couldn't process the image with my multimodal capabilities: {str(e)}",
            "error": str(e)
        }

def extract_json_from_response(response_text: str) -> Optional[Dict]:
    """Enhanced JSON extraction using Llama 4 Maverick's structured output"""
    import json
    import re
    
    try:
        # Method 1: Direct JSON extraction
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        # Method 2: Look for code blocks
        code_block_match = re.search(r'``````', response_text, re.DOTALL)
        if code_block_match:
            return json.loads(code_block_match.group(1))
        
        # Method 3: Multiple JSON objects (take first valid one)
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except:
                    continue
                    
    except Exception as e:
        logger.warning(f"JSON extraction failed: {e}")
    
    return None

def get_reasoning_chain(prompt: str, steps: List[str] = None) -> Dict:
    """
    Advanced step-by-step reasoning using Llama 4 Maverick
    """
    
    if not steps:
        steps = [
            "Understanding the problem",
            "Analyzing key components", 
            "Developing solution approach",
            "Implementing the solution",
            "Verifying the result"
        ]
    
    reasoning_prompt = f"""
    Use your advanced reasoning capabilities to solve this step-by-step:
    
    Problem: {prompt}
    
    Please work through this using the following steps:
    {chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}
    
    For each step, explain your reasoning clearly. Then provide your final answer.
    """
    
    return get_llm_response(
        reasoning_prompt,
        system_prompt="You are Alice using Llama 4 Maverick's advanced reasoning. Think step-by-step and show your work.",
        task_type="reasoning"
    )

# Performance monitoring
def get_model_info() -> Dict:
    """Get current model capabilities"""
    return {
        "model": LLM_MODEL,
        "capabilities": {
            "reasoning": "Advanced multi-step reasoning",
            "multimodal": "Native image understanding", 
            "context": f"{CONTEXT_WINDOW_SIZE:,} tokens",
            "languages": ["English", "Spanish", "French", "German", "Hindi", "Indonesian", "Italian", "Portuguese", "Tagalog", "Thai", "Vietnamese", "Arabic"],
            "fast_inference": True,
            "parameters": "17B mixture-of-experts (128 experts)"
        },
        "performance": {
            "inference_speed": "Ultra-fast with Groq",
            "reasoning_quality": "Industry-leading",
            "context_retention": "128K token memory"
        }
    }

logger.info(f"🚀 Llama 4 Maverick LLM system initialized: {LLM_MODEL}")
