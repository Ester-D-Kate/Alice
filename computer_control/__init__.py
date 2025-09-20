"""
🖥️ Alice Computer Control System
Remote computer automation with AI planning and visual feedback
"""

from .control_logic import get_computer_control, AliceComputerControl

__version__ = "2.0.0"
__description__ = "AI-powered computer control with multimodal feedback"

__all__ = [
    'get_computer_control',
    'AliceComputerControl'
]

# Initialize computer control system
import logging
logger = logging.getLogger(__name__)
logger.info("🖥️ Alice Computer Control System initialized")
