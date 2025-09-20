import logging
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import all API routers
from api.chat import router as chat_router
from api.search import router as search_router
from api.computer_control import router as computer_router
from api.templates import router as templates_router
from api.models import HealthResponse

# Import core components
from core.database_manager import get_db_manager
from core.context_analyzer import get_context_analyzer
from core.template_manager import get_template_manager
from computer_control.control_logic import get_computer_control
from llm import get_model_info
from config import ALICE_SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alice.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global startup time
startup_time = datetime.now()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Startup
    logger.info("🚀 Alice AI Assistant starting up...")
    
    try:
        # Initialize core components
        logger.info("🧠 Initializing AI brain components...")
        db = get_db_manager()
        context_analyzer = get_context_analyzer()
        template_manager = get_template_manager()
        computer_control = get_computer_control()
        
        logger.info("✅ All components initialized successfully")
        
        # Test LLM connection
        model_info = get_model_info()
        logger.info(f"🤖 {model_info['model']} ready with {model_info['capabilities']['parameters']}")
        
        logger.info("🎉 Alice AI Assistant is ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Alice AI Assistant shutting down...")
    
    try:
        # Close database connections
        db = get_db_manager()
        db.close_connections()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("👋 Alice AI Assistant stopped")

# Create FastAPI app
app = FastAPI(
    title="Alice AI Assistant",
    description="""
    🤖 **Alice AI Assistant** - Advanced Multimodal AI powered by Llama 4 Maverick
    
    ## Features
    - 🧠 **Advanced Reasoning**: Multi-step problem solving with 128K context
    - 🔍 **Intelligent Search**: Real-time web search integration
    - 🖥️ **Computer Control**: Remote computer automation with visual feedback
    - 🖼️ **Multimodal**: Native text and image understanding
    - 📋 **Learning**: Template creation and workflow automation
    - 🌍 **Multi-Language**: Support for 12 languages
    
    ## Powered By
    - **Llama 4 Maverick** (17B MoE with 128 experts)
    - **Groq** for ultra-fast inference
    - **PostgreSQL + pgvector** for intelligent memory
    - **Redis** for high-speed caching
    - **MQTT** for real-time device communication
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # Process request
    response = await call_next(request)
    
    # Log request details
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"🌐 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Alice encountered an internal error. Please try again.",
            "timestamp": datetime.now().isoformat()
        }
    )

# Include API routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(computer_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")

# Root endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """Alice AI Assistant - Root endpoint"""
    
    uptime = (datetime.now() - startup_time).total_seconds()
    model_info = get_model_info()
    
    return HealthResponse(
        success=True,
        service="Alice AI Assistant",
        version="2.0.0",
        model=model_info["model"],
        capabilities=[
            "Advanced Reasoning (Llama 4 Maverick)",
            "Multimodal Understanding",
            "Web Search Integration", 
            "Computer Control Automation",
            "Template Learning System",
            "128K Context Memory",
            "12 Language Support",
            "Ultra-Fast Groq Inference"
        ],
        uptime=uptime
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive system health check"""
    
    try:
        # Test core components
        db = get_db_manager()
        
        # Test database connectivity
        db.redis_conn.ping()
        
        # Test LLM connectivity
        model_info = get_model_info()
        
        uptime = (datetime.now() - startup_time).total_seconds()
        
        return HealthResponse(
            success=True,
            service="Alice AI Assistant",
            version="2.0.0", 
            model=model_info["model"],
            capabilities=list(model_info["capabilities"].values()),
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"System health check failed: {str(e)}"
        )

# API Info endpoint
@app.get("/api/info")
async def api_info():
    """Get comprehensive API information"""
    
    model_info = get_model_info()
    
    return {
        "success": True,
        "alice_info": {
            "version": "2.0.0",
            "description": "Advanced Multimodal AI Assistant",
            "model": model_info["model"],
            "capabilities": model_info["capabilities"],
            "performance": model_info["performance"]
        },
        "endpoints": {
            "chat": "/api/v1/chat/",
            "multimodal": "/api/v1/chat/multimodal",
            "search": "/api/v1/search/",
            "computer_control": "/api/v1/computer/execute",
            "screenshot": "/api/v1/computer/screenshot",
            "templates": "/api/v1/templates/",
            "devices": "/api/v1/computer/devices"
        },
        "features": {
            "reasoning": "Advanced multi-step problem solving",
            "multimodal": "Native text and image understanding",
            "search": "Real-time web search with DuckDuckGo",
            "automation": "Computer control with visual feedback",
            "learning": "Template creation and workflow automation",
            "memory": "128K context window with persistent learning",
            "languages": "12 supported languages",
            "inference": "Ultra-fast with Groq acceleration"
        }
    }

# WebSocket endpoint for real-time chat (optional)
@app.websocket("/ws/chat")
async def websocket_chat(websocket):
    """Real-time chat via WebSocket"""
    
    await websocket.accept()
    logger.info("🔌 WebSocket chat connection established")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process with Alice (simplified)
            response = {
                "success": True,
                "response": f"Alice received: {message_data.get('message', '')}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send response
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        logger.info("🔌 WebSocket chat connection closed")

if __name__ == "__main__":
    logger.info("🚀 Starting Alice AI Assistant server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info",
        access_log=True,
        loop="asyncio"
    )
