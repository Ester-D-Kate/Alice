import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from .models import SearchRequest, SearchResponse
from utils.search_integration import alice_search

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

async def track_processing_time():
    start_time = datetime.now()
    yield start_time

@router.post("/", response_model=SearchResponse)
async def web_search(
    request: SearchRequest,
    start_time: datetime = Depends(track_processing_time)
):
    """
    🔍 Web search endpoint using your DuckDuckGo search engine
    Fixed parameters: multiplier=5, required_results=2
    """
    
    try:
        logger.info(f"🔍 Search request: '{request.query}' (max_results: {request.max_results})")
        
        # Use your search integration with fixed parameters
        search_result = await alice_search(request.query)
        
        if not search_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {search_result.get('error', 'Unknown error')}"
            )
        
        # Limit results to requested amount
        results = search_result["results"][:request.max_results]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_found=len(results),
            search_params=search_result.get("search_params", {}),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions/{query}")
async def search_suggestions(query: str):
    """Get search suggestions (simple implementation)"""
    
    try:
        # Simple keyword-based suggestions
        suggestions = []
        
        query_lower = query.lower()
        
        # Add common search patterns
        if len(query) >= 3:
            common_patterns = [
                f"{query} tutorial",
                f"{query} guide",
                f"{query} examples",
                f"how to {query}",
                f"what is {query}",
                f"{query} 2025"
            ]
            suggestions.extend(common_patterns[:3])
        
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"❌ Search suggestions failed: {e}")
        return {
            "success": False,
            "query": query,
            "suggestions": [],
            "error": str(e)
        }
