"""
Test Alice Search Functionality
Tests the complete search pipeline
"""

import asyncio
import aiohttp
import json
import time

BASE_URL = "http://localhost:8000"


async def test_search_execute():
    """Test the search execute endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Search Execute Endpoint")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            request_data = {
                "query": "What is the weather in Jalandhar today?",
                "required_results": 3,
                "user_id": "test_user"
            }
            
            print(f"\n📤 Sending search request: {request_data['query']}")
            start_time = time.time()
            
            async with session.post(
                f"{BASE_URL}/api/v1/search/execute",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                result = await resp.json()
                elapsed = time.time() - start_time
                
                print(f"\n📥 Response received in {elapsed:.2f}s")
                print(f"✓ Success: {result.get('success')}")
                print(f"✓ Total Results: {result.get('total_results')}")
                print(f"✓ Processing Time: {result.get('processing_time'):.2f}s")
                
                if result.get('results'):
                    print(f"\n📊 Results:")
                    for i, r in enumerate(result['results'][:3], 1):
                        print(f"\n{i}. {r['title']}")
                        print(f"   URL: {r['url']}")
                        print(f"   Method: {r['method']}")
                        print(f"   Quality: {r['quality_score']}")
                        print(f"   Words: {r['word_count']}")
                        print(f"   Content: {r['content'][:200]}...")
                
                return result.get('success', False)
                
        except asyncio.TimeoutError:
            print("❌ Request timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_search_answer():
    """Test the search and answer endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Search + Answer Endpoint")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            request_data = {
                "query": "What is the current weather in Jalandhar?",
                "required_results": 5,
                "user_id": "test_user"
            }
            
            print(f"\n📤 Sending search+answer request: {request_data['query']}")
            start_time = time.time()
            
            async with session.post(
                f"{BASE_URL}/api/v1/search/answer",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                result = await resp.json()
                elapsed = time.time() - start_time
                
                print(f"\n📥 Response received in {elapsed:.2f}s")
                print(f"✓ Success: {result.get('success')}")
                print(f"✓ Processing Time: {result.get('processing_time'):.2f}s")
                print(f"✓ Total Sources: {result.get('total_sources')}")
                
                print(f"\n💬 Answer:")
                print(result.get('answer', 'No answer')[:500])
                
                if result.get('sources'):
                    print(f"\n📚 Sources Used:")
                    for source in result['sources'][:3]:
                        print(f"  {source['position']}. {source['title']}")
                        print(f"     {source['url']}")
                
                return result.get('success', False)
                
        except asyncio.TimeoutError:
            print("❌ Request timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_chat_integration():
    """Test the chat endpoint with search integration"""
    print("\n" + "="*60)
    print("TEST 3: Chat Endpoint with Search")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            request_data = {
                "message": "What's the weather like in Jalandhar today?",
                "user_id": "test_user"
            }
            
            print(f"\n📤 Sending chat message: {request_data['message']}")
            
            async with session.post(
                f"{BASE_URL}/api/v1/chat/message",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                result = await resp.json()
                
                print(f"\n📥 Chat Response:")
                print(f"✓ Success: {result.get('success')}")
                print(f"✓ Message: {result.get('message')}")
                print(f"✓ Task Completed: {result.get('task_completed')}")
                print(f"✓ Next Action: {result.get('next_action')}")
                
                if result.get('task_analysis'):
                    ta = result['task_analysis']
                    print(f"\n🧠 Task Analysis:")
                    print(f"  - Task Type: {ta.get('task_type')}")
                    print(f"  - Requires Search: {ta.get('requires_search')}")
                    print(f"  - Can Answer Directly: {ta.get('can_answer_directly')}")
                    print(f"  - Confidence: {ta.get('confidence')}")
                
                # If search is required, automatically call search endpoint
                if result.get('next_action') == 'search_agent':
                    print(f"\n🔍 Search required! Executing search...")
                    search_result = await test_search_answer()
                    return search_result
                
                return result.get('success', False)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_health_checks():
    """Test all health endpoints"""
    print("\n" + "="*60)
    print("TEST 0: Health Checks")
    print("="*60)
    
    endpoints = [
        "/",
        "/api/v1/chat/health",
        "/api/v1/search/health",
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(f"{BASE_URL}{endpoint}") as resp:
                    result = await resp.json()
                    print(f"✓ {endpoint}: {json.dumps(result, indent=2)}")
            except Exception as e:
                print(f"❌ {endpoint}: {e}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🤖 ALICE SEARCH FUNCTIONALITY TEST SUITE")
    print("="*70)
    print("\nMake sure Alice is running: python main.py")
    print("Press Ctrl+C to cancel\n")
    
    await asyncio.sleep(2)
    
    # Test 0: Health checks
    await test_health_checks()
    
    # Test 1: Search Execute
    test1_passed = await test_search_execute()
    
    # Test 2: Search + Answer
    test2_passed = await test_search_answer()
    
    # Test 3: Chat Integration
    test3_passed = await test_chat_integration()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Health Checks: ✓")
    print(f"Search Execute: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Search + Answer: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"Chat Integration: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
