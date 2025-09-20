"""
Alice FastAPI Endpoints
RESTful API for Alice AI Assistant
"""

from .models import *

__version__ = "2.0.0"
__description__ = "Alice AI Assistant API"

__all__ = [
    'ChatRequest', 'ChatResponse',
    'SearchRequest', 'SearchResponse', 
    'ComputerControlRequest', 'ComputerControlResponse',
    'HealthResponse', 'ErrorResponse'
]

import logging
logger = logging.getLogger(__name__)
logger.info("Alice API endpoints initialized")
