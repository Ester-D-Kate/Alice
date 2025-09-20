"""
🔍 Alice Search Integration - FIXED VERSION
Wrapper for your existing DuckDuckGo search system
Fixed parameters: multiplier=5, required_results=2
"""

import logging
import asyncio
from typing import Dict
from typing import Dict, List  # Add List import

# Import your search engine directly - NO circular imports
try:
    from utils.search.search_engine import search_web_enhanced
    SEARCH_AVAILABLE = True
    print("✅ Alice search engine loaded successfully")
except ImportError as e:
    print(f"⚠️ Search engine import failed: {e}")
    SEARCH_AVAILABLE = False

from config import SEARCH_MULTIPLIER, SEARCH_REQUIRED_RESULTS

logger = logging.getLogger(__name__)

async def alice_search(query: str) -> Dict:
    """
    🔍 Alice's search function - integrates with your existing search system
    
    Fixed parameters as requested:
    - multiplier = 5 (always)
    - required_results = 2 (always)
    """
    
    if not SEARCH_AVAILABLE:
        return {
            "success": False,
            "error": "Search engine not available",
            "query": query,
            "results": [],
            "search_params": {
                "required_results": SEARCH_REQUIRED_RESULTS,
                "multiplier": SEARCH_MULTIPLIER
            }
        }
    
    try:
        logger.info(f"🔍 Alice searching: '{query}' (multiplier={SEARCH_MULTIPLIER}, results={SEARCH_REQUIRED_RESULTS})")
        
        # Use your existing search engine with fixed parameters
        results = await search_web_enhanced(
            query=query,
            required_results=SEARCH_REQUIRED_RESULTS,  # Always 2
            url_multiplier=SEARCH_MULTIPLIER           # Always 5
        )
        
        # Process results for Alice
        processed_results = []
        for i, result in enumerate(results[:SEARCH_REQUIRED_RESULTS]):
            processed_result = {
                "rank": i + 1,
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "No description available"),
                "source": result.get("source", "web"),
                "relevance_score": result.get("relevance_score", 0.0),
                "timestamp": result.get("timestamp")
            }
            processed_results.append(processed_result)
        
        logger.info(f"✅ Alice search completed: {len(processed_results)} results")
        
        return {
            "success": True,
            "query": query,
            "results": processed_results,
            "total_found": len(processed_results),
            "search_params": {
                "required_results": SEARCH_REQUIRED_RESULTS,
                "multiplier": SEARCH_MULTIPLIER,
                "search_engine": "DuckDuckGo",
                "alice_enhanced": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Alice search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": [],
            "search_params": {
                "required_results": SEARCH_REQUIRED_RESULTS,
                "multiplier": SEARCH_MULTIPLIER
            }
        }

logger.info("🔍 Alice Search Integration initialized")
