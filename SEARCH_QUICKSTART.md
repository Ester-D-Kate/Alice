# Alice Search Functionality - Quick Start Guide

## 🚀 What Was Fixed

### Issues Resolved:
1. ✅ **Unclosed aiohttp sessions** - All HTTP sessions now close properly
2. ✅ **Crawl4AI shutdown** - Proper cleanup on application shutdown
3. ✅ **Hugging Face timeout** - Added retry logic with exponential backoff
4. ✅ **Missing Search API** - Created complete search endpoints

### New Features Added:
- 📡 `/api/v1/search/execute` - Execute web search and return results
- 🤖 `/api/v1/search/answer` - Search + AI answer generation
- 🔗 Integrated search into chat flow

---

## 📦 Installation

### 1. Install Dependencies (if needed)
```powershell
cd "c:\Users\mahaj\OneDrive\Documents\Projects\Alice"
pip install fastapi uvicorn aiohttp duckduckgo-search beautifulsoup4 qdrant-client sentence-transformers python-dotenv groq
```

### 2. Optional: Install Crawl4AI for better scraping
```powershell
pip install crawl4ai
```

---

## 🎯 Running Alice

### Start the Server
```powershell
cd "c:\Users\mahaj\OneDrive\Documents\Projects\Alice"
python main.py
```

Or with uvicorn for auto-reload:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

---

## 🧪 Testing

### Run Complete Test Suite
```powershell
cd "c:\Users\mahaj\OneDrive\Documents\Projects\Alice"
python test_search.py
```

This will test:
- ✓ Health endpoints
- ✓ Search execution
- ✓ Search + Answer
- ✓ Chat integration

---

## 📡 API Endpoints

### 1. Chat Endpoint
**POST** `/api/v1/chat/message`

```json
{
  "message": "What's the weather in Jalandhar?",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Let me search for that information...",
  "task_analysis": {
    "task_type": "search_required",
    "requires_search": 1,
    "can_answer_directly": 0,
    "confidence": 0.95
  },
  "task_completed": false,
  "next_action": "search_agent"
}
```

### 2. Search Execute Endpoint
**POST** `/api/v1/search/execute`

```json
{
  "query": "weather in Jalandhar today",
  "required_results": 5,
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "query": "weather in Jalandhar today",
  "results": [
    {
      "title": "Jalandhar Weather - Current Conditions",
      "url": "https://example.com/weather",
      "content": "The current weather in Jalandhar is...",
      "method": "BeautifulSoup",
      "quality_score": 85,
      "word_count": 234
    }
  ],
  "total_results": 5,
  "processing_time": 3.45
}
```

### 3. Search + Answer Endpoint (Recommended)
**POST** `/api/v1/search/answer`

```json
{
  "query": "What is the weather in Jalandhar?",
  "required_results": 5,
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What is the weather in Jalandhar?",
  "answer": "Based on current data, the weather in Jalandhar is...",
  "sources": [
    {
      "title": "Weather Source 1",
      "url": "https://example.com/weather",
      "position": 1
    }
  ],
  "total_sources": 5,
  "processing_time": 4.67
}
```

---

## 🔧 How It Works

### Flow Diagram:
```
User Query
    ↓
Chat Endpoint (/api/v1/chat/message)
    ↓
Task Analyzer (LLM analyzes if search is needed)
    ↓
If search_required:
    → Search Execute (/api/v1/search/execute)
        → DuckDuckGo Search
        → LLM URL Ranking
        → Parallel Scraping (BeautifulSoup/Playwright/Crawl4AI)
        → Quality Assessment
        → Return Top Results
    ↓
Search + Answer (/api/v1/search/answer)
    → Takes search results
    → Generates AI answer
    → Returns formatted response
```

### Pipeline Components:

1. **Search Engine** (`utils/search/search_engine.py`)
   - Uses DuckDuckGo for web search
   - Returns multiplied URLs for ranking

2. **LLM Ranker** (`utils/search/llm_ranker.py`)
   - Ranks URLs by relevance
   - Selects best scraping method per URL

3. **Scrapers** (`utils/search/scraper.py`)
   - BeautifulSoup (fast, simple sites)
   - Playwright (JavaScript-heavy sites)
   - Crawl4AI (complex content extraction)

4. **Quality Assessment**
   - Word count analysis
   - Content quality scoring
   - Domain reputation

---

## 🐛 Debugging

### Check Server Logs
The server will log all operations:
```
INFO: Search request from user123: What's the weather...
INFO: 🔍 DuckDuckGo search for: 'weather in Jalandhar'
INFO: ✅ Search completed: 5 URLs found
INFO: 🧠 LLM: Ranking URLs + method selection...
INFO: 🚀 ULTRA-PARALLEL PROCESSING...
INFO: ✅ Search completed: 5 results in 4.23s
```

### Common Issues:

1. **"No results found"**
   - Check internet connection
   - Verify DuckDuckGo is accessible
   - Try different search query

2. **Timeout errors**
   - Increase timeout in test script
   - Check if scraping targets are slow
   - Reduce `required_results`

3. **"Crawl4AI not available"**
   - This is normal if not installed
   - System will use BeautifulSoup/Playwright
   - Install with: `pip install crawl4ai`

4. **Hugging Face timeout**
   - Retry logic will handle this automatically
   - Model downloads on first run only
   - Subsequent runs use cached model

---

## 📊 Performance

### Expected Timings:
- Simple search (3 results): 2-5 seconds
- Full search (5 results): 3-8 seconds
- Complex search (10 results): 5-15 seconds

### Optimization Tips:
1. Reduce `required_results` for faster responses
2. Use `url_multiplier=5` instead of 10 for speed
3. Ensure Playwright is installed for better success rate
4. Pre-warm the system on startup (happens automatically)

---

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Server starts without errors
- ✅ Health check returns 200 OK
- ✅ Test suite passes all tests
- ✅ Search returns results within timeout
- ✅ No "Unclosed client session" warnings
- ✅ Clean shutdown with "Crawl4AI shut down cleanly"

---

## 📞 Support

If issues persist:
1. Check `FIXES_APPLIED.md` for detailed fixes
2. Review server logs for specific errors
3. Run test suite to identify failing component
4. Verify all dependencies are installed

---

## 🚀 Next Steps

1. **Improve Answer Generation**: Add better LLM prompts for answer synthesis
2. **Add Caching**: Cache search results for common queries
3. **Implement Rate Limiting**: Protect against abuse
4. **Add More Sources**: Integrate additional search engines
5. **Vector Search**: Use Qdrant for semantic search across history

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Production Ready
