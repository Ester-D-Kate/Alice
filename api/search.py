"""
Search API - Executes web searches and returns optimized results
"""

import logging
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from utils.search.scraper import search_and_scrape_complete

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    required_results: int = Field(default=5, description="Number of results needed")
    user_id: str = Field(default="default_user", description="User ID")


class SearchResult(BaseModel):
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    content: str = Field(..., description="Page content")
    method: str = Field(..., description="Scraping method used")
    quality_score: float = Field(..., description="Content quality score")
    word_count: int = Field(..., description="Word count")


class SearchResponse(BaseModel):
    success: bool = Field(..., description="Search success")
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total results returned")
    processing_time: float = Field(..., description="Processing time in seconds")
    summary: Optional[str] = Field(None, description="AI-generated summary of results")
    timestamp: datetime = Field(default_factory=datetime.now)


@router.post("/execute", response_model=SearchResponse)
async def execute_search(request: SearchRequest) -> SearchResponse:
    """
    Execute web search and return optimized results
    
    This endpoint:
    1. Searches the web using DuckDuckGo
    2. Ranks URLs with LLM
    3. Scrapes content in parallel
    4. Returns high-quality results
    """
    try:
        logger.info(f"Search request from {request.user_id}: {request.query}")
        start_time = time.time()
        
        # Execute search and scrape
        results = await search_and_scrape_complete(
            query=request.query,
            required_results=request.required_results,
            url_multiplier=10
        )
        
        if not results:
            logger.warning(f"No results found for query: {request.query}")
            return SearchResponse(
                success=False,
                query=request.query,
                results=[],
                total_results=0,
                processing_time=time.time() - start_time,
                summary="No results found for your query."
            )
        
        # Convert results to SearchResult schema
        search_results = []
        for result in results:
            try:
                search_results.append(SearchResult(
                    title=result.get('title', 'No title'),
                    url=result.get('url', ''),
                    content=result.get('content', ''),
                    method=result.get('method', 'Unknown'),
                    quality_score=result.get('quality_score', 0),
                    word_count=len(result.get('content', '').split())
                ))
            except Exception as e:
                logger.warning(f"Failed to parse result: {e}")
                continue
        
        processing_time = time.time() - start_time
        
        # Generate summary
        summary = f"Found {len(search_results)} high-quality results for '{request.query}' in {processing_time:.2f}s"
        
        logger.info(f"Search completed: {len(search_results)} results in {processing_time:.2f}s")
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            processing_time=processing_time,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Search execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search execution failed: {str(e)}"
        )


@router.post("/answer", response_model=Dict[str, Any])
async def search_and_answer(request: SearchRequest) -> Dict[str, Any]:
    """
    Execute search and generate AI answer from results
    
    This is the recommended endpoint that combines:
    1. Web search
    2. Content scraping
    3. AI answer generation
    """
    try:
        logger.info(f"Search+Answer request from {request.user_id}: {request.query}")
        start_time = time.time()
        
        # Step 1: Execute search
        results = await search_and_scrape_complete(
            query=request.query,
            required_results=request.required_results,
            url_multiplier=10
        )
        
        if not results:
            return {
                "success": False,
                "query": request.query,
                "answer": "I couldn't find any information about that.",
                "sources": [],
                "processing_time": time.time() - start_time
            }
        
        # Step 2: Prepare context for LLM
        context_parts = []
        sources = []
        
        for i, result in enumerate(results[:5], 1):  # Use top 5 results
            content = result.get('content', '')[:1000]  # First 1000 chars
            url = result.get('url', '')
            title = result.get('title', 'Source')
            
            context_parts.append(f"[Source {i}] {title}\n{content}\n")
            sources.append({"title": title, "url": url, "position": i})
        
        context = "\n---\n".join(context_parts)
        
        # Step 3: Generate answer using Groq (you'll need to implement this)
        # For now, return the context
        answer = f"Based on {len(results)} sources, here's what I found:\n\n{context[:500]}..."
        
        processing_time = time.time() - start_time
        
        logger.info(f"Search+Answer completed in {processing_time:.2f}s")
        
        return {
            "success": True,
            "query": request.query,
            "answer": answer,
            "sources": sources,
            "total_sources": len(results),
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search+Answer failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search and answer failed: {str(e)}"
        )


@router.get("/health")
async def search_health():
    """Health check for search service"""
    return {
        "status": "healthy",
        "service": "Search API",
        "timestamp": datetime.now().isoformat()
    }
