"""
🧠 Alice Intelligence Core
Advanced AI reasoning, context analysis, and learning systems
"""

from .database_manager import get_db_manager, AliceDatabaseManager
from .context_analyzer import get_context_analyzer, AliceContextAnalyzer
from .template_manager import get_template_manager, AliceTemplateManager

__version__ = "2.0.0"
__author__ = "Alice AI Team"

__all__ = [
    'get_db_manager',
    'AliceDatabaseManager',
    'get_context_analyzer', 
    'AliceContextAnalyzer',
    'get_template_manager',
    'AliceTemplateManager'
]

# Initialize core components on import
import logging
logger = logging.getLogger(__name__)
logger.info("🧠 Alice Intelligence Core initialized")
