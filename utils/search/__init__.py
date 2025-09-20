"""
🔍 Alice Search System - Your DuckDuckGo Search Engine
Fixed for Alice AI integration
"""

# Import your existing search functions directly
from .search_engine import (
    search_web_enhanced,
    search_duckduckgo,
    search_web
)

from .scraper import (
    scrape_single_url,
    search_and_scrape_complete,
    scrape_simple_website
)

from .playwright_scraper import (
    scrape_javascript_website, 
    should_use_playwright, 
    PLAYWRIGHT_AVAILABLE
)

from .crawl4ai_scraper import (
    scrape_with_crawl4ai, 
    should_use_crawl4ai, 
    CRAWL4AI_AVAILABLE
)

from .llm_ranker import (
    rank_urls_with_llm, 
    simple_rank_urls
)

from .hardware_monitor import (
    get_simple_hardware_info,
    can_handle_parallel,
    get_optimal_parallel_count,
    print_hardware_status
)

from .search_config import (
    get_config, 
    print_config_status
)

# Export main functions Alice needs
__all__ = [
    'search_web_enhanced',
    'search_duckduckgo', 
    'search_web',
    'scrape_single_url',
    'search_and_scrape_complete'
]

print("🔍 Alice Search System loaded successfully")
