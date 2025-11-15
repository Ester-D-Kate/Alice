"""
Alice - Clean Version
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.audio_processing import router as audio_router
from api.search import router as search_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Alice AI Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
app.include_router(chat_router, prefix="/api/v1")      # Text input
app.include_router(audio_router, prefix="/api/v1")     # Audio input
app.include_router(search_router, prefix="/api/v1")    # Search & scrape

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logging.info("Shutting down Alice AI Assistant...")
    try:
        # Import and shutdown Crawl4AI if it's being used
        from utils.search.crawl4ai_scraper import shutdown_crawl4ai, CRAWL4AI_AVAILABLE
        if CRAWL4AI_AVAILABLE:
            await shutdown_crawl4ai()
    except ImportError:
        pass
    except Exception as e:
        logging.warning(f"Error during shutdown cleanup: {e}")
    logging.info("Cleanup complete")

@app.get("/")
async def root():
    return {
        "message": "Alice AI Assistant", 
        "version": "1.0.0",
        "endpoints": {
            "text_chat": "/api/v1/chat/message",
            "voice_chat": "/api/v1/audio/process",
            "search_execute": "/api/v1/search/execute",
            "search_answer": "/api/v1/search/answer",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
