#!/usr/bin/env python3
"""
🔥 ALICE AI ASSISTANT - COMPLETE SYSTEM VERIFICATION
Tests every component before launch to ensure 100% functionality
"""

# Add this at the very top of alice_full_verification.py
import sys
import os
sys.path.insert(0, os.getcwd())

import json
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

class AliceSystemVerifier:
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.verbose = True
        print("🤖 ALICE AI ASSISTANT - FULL SYSTEM VERIFICATION")
        print("=" * 60)
        print(f"🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result with detailed information"""
        status = "✅ PASS" if success else "❌ FAIL"
        
        if self.verbose:
            print(f"{status} {test_name}")
            if details:
                print(f"    📝 {details}")
            if error and not success:
                print(f"    ❌ Error: {error}")
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        return success
    
    def test_environment(self) -> bool:
        """Test 1: Environment Variables & Configuration"""
        print("🔧 TESTING ENVIRONMENT & CONFIGURATION")
        print("-" * 40)
        
        required_vars = [
            "GROQ_API_KEY", "PG_HOST", "PG_DATABASE", "PG_USER", "PG_PASSWORD", "PG_PORT",
            "REDIS_HOST", "REDIS_PORT", "SEARCH_MULTIPLIER", "SEARCH_REQUIRED_RESULTS"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif self.verbose:
                masked_value = value if var not in ["GROQ_API_KEY", "PG_PASSWORD"] else f"{value[:10]}..."
                print(f"    {var}: {masked_value}")
        
        if missing_vars:
            return self.log_test("Environment Variables", False, 
                               error=f"Missing variables: {', '.join(missing_vars)}")
        
        return self.log_test("Environment Variables", True, 
                           f"All {len(required_vars)} required variables present")
    
    def test_imports(self) -> bool:
        """Test 2: Import All Alice Components"""
        print("\n📦 TESTING IMPORTS & DEPENDENCIES")
        print("-" * 40)
        
        import_tests = [
            ("config", "import config"),
            ("LLM Core", "from llm import get_llm_response, get_model_info"),
            ("Database Manager", "from core.database_manager import get_db_manager"),
            ("Context Analyzer", "from core.context_analyzer import get_context_analyzer"),
            ("Template Manager", "from core.template_manager import get_template_manager"),
            ("Computer Control", "from computer_control.control_logic import get_computer_control"),
            ("Search Integration", "from utils.search_integration import alice_search"),
            ("API Models", "from api.models import ChatRequest, ChatResponse"),
            ("FastAPI Core", "from fastapi import FastAPI"),
            ("Required Libraries", "import psycopg2, redis, groq")
        ]
        
        failed_imports = []
        
        for module_name, import_statement in import_tests:
            try:
                exec(import_statement)
                self.log_test(f"Import: {module_name}", True)
            except Exception as e:
                self.log_test(f"Import: {module_name}", False, error=str(e))
                failed_imports.append(module_name)
        
        return len(failed_imports) == 0
    
    def test_databases(self) -> bool:
        """Test 3: Database Connections (PostgreSQL + Redis)"""
        print("\n🗄️ TESTING DATABASE CONNECTIONS")
        print("-" * 40)
        
        # Test PostgreSQL
        pg_success = False
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('PG_HOST'),
                database=os.getenv('PG_DATABASE'),
                user=os.getenv('PG_USER'),
                password=os.getenv('PG_PASSWORD'),
                port=int(os.getenv('PG_PORT')),
                connect_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            pg_success = self.log_test("PostgreSQL Connection", True, 
                                     f"Connected to {os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}")
            
        except Exception as e:
            self.log_test("PostgreSQL Connection", False, error=str(e))
        
        # Test Redis
        redis_success = False
        try:
            import redis
            r = redis.Redis(
                host=os.getenv('REDIS_HOST'),
                port=int(os.getenv('REDIS_PORT')),
                db=int(os.getenv('REDIS_DB', '0')),
                decode_responses=True,
                socket_connect_timeout=5
            )
            response = r.ping()
            r.close()
            
            redis_success = self.log_test("Redis Connection", True,
                                        f"Connected to {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
            
        except Exception as e:
            self.log_test("Redis Connection", False, error=str(e))
        
        return pg_success and redis_success
    
    def test_llm_system(self) -> bool:
        """Test 4: LLM System (Groq + Llama 4 Maverick)"""
        print("\n🧠 TESTING LLM SYSTEM")
        print("-" * 40)
        
        try:
            from llm import get_llm_response, get_model_info
            
            # Test model info
            model_info = get_model_info()
            self.log_test("LLM Model Info", True, 
                         f"Model: {model_info['model']}, Context: {model_info['capabilities']['context']}")
            
            # Test basic LLM call
            test_prompt = "Respond with exactly: 'Alice verification test successful'"
            result = get_llm_response(test_prompt, task_type="conversation", temperature=0.1)
            
            if result["success"]:
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                self.log_test("LLM Response Test", True, 
                             f"Response received: {response_preview}")
                return True
            else:
                self.log_test("LLM Response Test", False, error=result.get("error", "Unknown error"))
                return False
                
        except Exception as e:
            self.log_test("LLM System", False, error=str(e))
            return False
    
    def test_search_system(self) -> bool:
        """Test 5: Search System (DuckDuckGo Integration)"""
        print("\n🔍 TESTING SEARCH SYSTEM")
        print("-" * 40)
        
        try:
            from utils.search_integration import alice_search
            
            async def run_search_test():
                result = await alice_search("artificial intelligence test")
                return result
            
            search_result = asyncio.run(run_search_test())
            
            if search_result["success"]:
                params = search_result["search_params"]
                results_count = len(search_result["results"])
                
                # Verify parameters are correct
                if params["multiplier"] == 5 and params["required_results"] == 2:
                    self.log_test("Search System", True,
                                f"Found {results_count} results (multiplier=5, required=2)")
                    return True
                else:
                    self.log_test("Search System", False, 
                                error=f"Wrong parameters: multiplier={params['multiplier']}, required={params['required_results']}")
                    return False
            else:
                self.log_test("Search System", False, error=search_result.get("error", "Unknown error"))
                return False
                
        except Exception as e:
            self.log_test("Search System", False, error=str(e))
            return False
    
    def test_core_components(self) -> bool:
        """Test 6: Alice Core Components (Database, Context, Templates)"""
        print("\n🎯 TESTING CORE ALICE COMPONENTS")
        print("-" * 40)
        
        # Test Database Manager
        db_success = False
        try:
            from core.database_manager import get_db_manager
            db = get_db_manager()
            
            # Test conversation storage
            conv_id = db.store_conversation(
                user_id="verification_test",
                user_message="Test message for verification",
                alice_response="Test response for verification",
                intent="testing",
                confidence=0.99
            )
            
            # Test context retrieval
            context = db.get_conversation_context("verification_test", limit=1)
            
            db_success = self.log_test("Database Manager", True,
                                     f"Stored conversation {conv_id}, retrieved {len(context)} messages")
            
        except Exception as e:
            self.log_test("Database Manager", False, error=str(e))
        
        # Test Context Analyzer
        context_success = False
        try:
            from core.context_analyzer import get_context_analyzer
            analyzer = get_context_analyzer()
            
            intent_result = analyzer.analyze_user_intent(
                "Can you help me open a text editor?", "verification_test"
            )
            
            context_success = self.log_test("Context Analyzer", True,
                                          f"Intent: {intent_result['intent']}, Confidence: {intent_result['confidence']:.2f}")
            
        except Exception as e:
            self.log_test("Context Analyzer", False, error=str(e))
        
        # Test Template Manager
        template_success = False
        try:
            from core.template_manager import get_template_manager
            template_mgr = get_template_manager()
            
            template_success = self.log_test("Template Manager", True, "Initialized successfully")
            
        except Exception as e:
            self.log_test("Template Manager", False, error=str(e))
        
        return db_success and context_success and template_success
    
    def test_computer_control(self) -> bool:
        """Test 7: Computer Control System"""
        print("\n🖥️ TESTING COMPUTER CONTROL SYSTEM")
        print("-" * 40)
        
        try:
            from computer_control.control_logic import get_computer_control
            computer_control = get_computer_control()
            
            # Test basic initialization
            status = computer_control.get_device_status("test_device")
            
            self.log_test("Computer Control", True, "Initialized successfully")
            return True
            
        except Exception as e:
            self.log_test("Computer Control", False, error=str(e))
            return False
    
    def test_api_components(self) -> bool:
        """Test 8: API Components & Models"""
        print("\n🌐 TESTING API COMPONENTS")
        print("-" * 40)
        
        try:
            from api.models import ChatRequest, ChatResponse, SearchRequest, SearchResponse
            from api.chat import router as chat_router
            from api.search import router as search_router
            
            # Test model creation
            chat_req = ChatRequest(message="test", user_id="test")
            search_req = SearchRequest(query="test")
            
            self.log_test("API Models", True, "Pydantic models working")
            self.log_test("API Routers", True, "FastAPI routers loaded")
            return True
            
        except Exception as e:
            self.log_test("API Components", False, error=str(e))
            return False
    
    def test_fastapi_server(self) -> bool:
        """Test 9: FastAPI Server Initialization"""
        print("\n🚀 TESTING FASTAPI SERVER")
        print("-" * 40)
        
        try:
            # Import main FastAPI app
            import main
            
            self.log_test("FastAPI Server", True, "Main application imported successfully")
            return True
            
        except Exception as e:
            self.log_test("FastAPI Server", False, error=str(e))
            return False
    
    def run_full_verification(self) -> dict:
        """Run complete Alice verification"""
        
        print("🔥 STARTING FULL ALICE VERIFICATION")
        print("=" * 60)
        
        # Run all tests
        tests = [
            ("Environment", self.test_environment),
            ("Imports", self.test_imports),
            ("Databases", self.test_databases),
            ("LLM System", self.test_llm_system),
            ("Search System", self.test_search_system),
            ("Core Components", self.test_core_components),
            ("Computer Control", self.test_computer_control),
            ("API Components", self.test_api_components),
            ("FastAPI Server", self.test_fastapi_server)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} crashed: {str(e)}")
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Final report
        print("\n" + "=" * 60)
        print("🏆 ALICE AI VERIFICATION RESULTS")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_name}")
            if not result["success"] and result["error"]:
                print(f"    💥 {result['error']}")
        
        print(f"\n📊 SUMMARY:")
        print(f"    Total Tests: {total_tests}")
        print(f"    Passed: {passed_tests}")
        print(f"    Failed: {total_tests - passed_tests}")
        print(f"    Success Rate: {success_rate:.1f}%")
        print(f"    Duration: {duration:.2f} seconds")
        
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print(f"\n🎉 ALICE IS 100% READY FOR LAUNCH! 🚀")
            print(f"🔥 All systems operational - Ready to serve!")
        else:
            print(f"\n⚠️ ALICE HAS ISSUES - {total_tests - passed_tests} TESTS FAILED")
            print(f"🔧 Fix failed components before launching Alice")
        
        return {
            "overall_success": overall_success,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "duration": duration,
            "detailed_results": self.test_results,
            "ready_for_launch": overall_success
        }

def main():
    """Main verification runner"""
    
    print("🤖 ALICE AI ASSISTANT - COMPLETE SYSTEM VERIFICATION")
    print("🔥 Testing every component before launch...")
    print()
    
    verifier = AliceSystemVerifier()
    results = verifier.run_full_verification()
    
    # Save results
    with open("alice_verification_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved: alice_verification_results.json")
    
    if results["ready_for_launch"]:
        print("\n🚀 ALICE IS READY!")
        launch = input("\nStart Alice server now? (y/n): ").lower().strip()
        if launch in ['y', 'yes']:
            print("\n🎉 Launching Alice AI Assistant...")
            print("🌐 Starting server on: http://localhost:8000")
            print("📋 API docs will be at: http://localhost:8000/docs")
            print("\n⚡ Run this command:")
            print("    python main.py")
        else:
            print("✅ Alice verified and ready. Launch when ready with: python main.py")
    else:
        print("\n🔧 Fix the issues above before launching Alice")
    
    return 0 if results["ready_for_launch"] else 1

if __name__ == "__main__":
    exit(main())
