"""
🔧 Core Alice Configuration
Centralized configuration for Alice's brain components
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Core AI Configuration
ALICE_CORE_VERSION = "2.0.0"
ALICE_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Advanced Learning Settings
LEARNING_ENABLED = True
TEMPLATE_AUTO_CREATION = True
CONTEXT_MEMORY_LIMIT = 50  # Number of conversations to remember
SIMILARITY_THRESHOLD = 0.7  # For template matching

# Intent Analysis Configuration
INTENT_CONFIDENCE_THRESHOLD = 0.6
CONTEXT_ANALYSIS_DEPTH = 3  # How many past conversations to analyze

# Template System Configuration
TEMPLATE_USAGE_TRACKING = True
TEMPLATE_IMPROVEMENT_ENABLED = True
MAX_TEMPLATES_PER_USER = 100

# Database Optimization Settings
VECTOR_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
BATCH_PROCESSING_SIZE = 10

# Cache Configuration
REDIS_CACHE_TTL = 3600  # 1 hour
CONVERSATION_CACHE_LIMIT = 10
ANALYSIS_CACHE_TTL = 1800  # 30 minutes

print("🔧 Alice Core configuration loaded")
