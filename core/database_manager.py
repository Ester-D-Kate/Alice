import psycopg2
from pgvector.psycopg2 import register_vector
import redis
import json
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
from config import PG_HOST, PG_DATABASE, PG_USER, PG_PASSWORD, PG_PORT, REDIS_HOST, REDIS_PORT, REDIS_DB

logger = logging.getLogger(__name__)

class AliceDatabaseManager:
    def __init__(self):
        # PostgreSQL connection with pgvector
        try:
            self.pg_conn = psycopg2.connect(
                host=PG_HOST,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD,
                port=PG_PORT
            )
            register_vector(self.pg_conn)
            self.create_tables()
            logger.info(f"✅ Connected to PostgreSQL: {PG_HOST}:{PG_DATABASE}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise

        # Redis for caching
        try:
            self.redis_conn = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_conn.ping()
            logger.info(f"✅ Connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

        # Embedding model for semantic search
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Embedding model failed: {e}")
            raise

    def create_tables(self):
        """Create all necessary database tables"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255),
                    user_message TEXT NOT NULL,
                    alice_response TEXT NOT NULL,
                    intent VARCHAR(100),
                    confidence FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    embedding vector(384),
                    context_data JSONB,
                    success BOOLEAN DEFAULT true
                );
            """)

            # Templates table  
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    trigger_patterns TEXT[],
                    execution_steps JSONB NOT NULL,
                    success_rate FLOAT DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    embedding vector(384)
                );
            """)

            # Computer executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS computer_executions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255),
                    task_description TEXT NOT NULL,
                    device_id VARCHAR(255),
                    execution_plan JSONB,
                    result JSONB,
                    success BOOLEAN,
                    execution_time FLOAT,
                    screenshots_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # User contexts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_contexts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    context_type VARCHAR(100),
                    context_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
                CREATE INDEX IF NOT EXISTS idx_templates_name ON templates(name);
                CREATE INDEX IF NOT EXISTS idx_executions_user_id ON computer_executions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_contexts_user_id ON user_contexts(user_id);
            """)

            self.pg_conn.commit()
            logger.info("✅ Database tables created/verified")
            
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"❌ Table creation failed: {e}")
            raise
        finally:
            cursor.close()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * 384  # Default zero embedding

    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        alice_response: str,
        intent: str = None,
        confidence: float = None,
        context_data: Dict = None,
        success: bool = True
    ) -> str:
        """Store conversation in database"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            conversation_id = str(uuid.uuid4())
            embedding = self.generate_embedding(user_message)
            
            cursor.execute("""
                INSERT INTO conversations (
                    id, user_id, user_message, alice_response, 
                    intent, confidence, embedding, context_data, success
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                conversation_id, user_id, user_message, alice_response,
                intent, confidence, embedding, json.dumps(context_data or {}), success
            ))
            
            self.pg_conn.commit()
            
            # Cache recent conversations
            cache_key = f"recent_conversations:{user_id}"
            recent = self.redis_conn.lpush(cache_key, json.dumps({
                'id': conversation_id,
                'message': user_message,
                'response': alice_response,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Keep only last 10
            self.redis_conn.ltrim(cache_key, 0, 9)
            self.redis_conn.expire(cache_key, 3600)  # 1 hour
            
            logger.info(f"✅ Conversation stored: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"❌ Conversation storage failed: {e}")
            raise
        finally:
            cursor.close()

    def get_conversation_context(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversation context for user"""
        
        # Try cache first
        cache_key = f"recent_conversations:{user_id}"
        cached = self.redis_conn.lrange(cache_key, 0, limit - 1)
        
        if cached:
            try:
                return [json.loads(item) for item in cached]
            except Exception as e:
                logger.warning(f"Cache parse error: {e}")
        
        # Fallback to database
        cursor = self.pg_conn.cursor()
        
        try:
            cursor.execute("""
                SELECT user_message, alice_response, created_at, intent
                FROM conversations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'message': row[0],
                    'response': row[1],
                    'timestamp': row[2].isoformat(),
                    'intent': row[3]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            return []
        finally:
            cursor.close()

    def find_similar_conversations(self, message: str, user_id: str = None, limit: int = 3) -> List[Dict]:
        """Find similar conversations using vector search"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            embedding = self.generate_embedding(message)
            
            # Query with vector similarity using proper casting
            query = """
                SELECT id, user_message, alice_response, intent, 
                       (embedding <-> %s::vector) as similarity
                FROM conversations 
                WHERE (embedding <-> %s::vector) < 0.8
            """
            params = [embedding, embedding]
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            query += " ORDER BY similarity LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'message': row[1],
                    'response': row[2],
                    'intent': row[3],
                    'similarity': float(row[4])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Similar conversation search failed: {e}")
            return []
        finally:
            cursor.close()

    def store_template(
        self,
        name: str,
        description: str,
        trigger_patterns: List[str],
        execution_steps: Dict,
        created_by: str = None
    ) -> str:
        """Store execution template"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            template_id = str(uuid.uuid4())
            embedding = self.generate_embedding(f"{name} {description}")
            
            cursor.execute("""
                INSERT INTO templates (
                    id, name, description, trigger_patterns, 
                    execution_steps, created_by, embedding
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                template_id, name, description, trigger_patterns,
                json.dumps(execution_steps), created_by, embedding
            ))
            
            self.pg_conn.commit()
            logger.info(f"✅ Template stored: {name}")
            return template_id
            
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"❌ Template storage failed: {e}")
            raise
        finally:
            cursor.close()

    def find_matching_template(self, task_description: str) -> Optional[Dict]:
        """Find template matching task description"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            embedding = self.generate_embedding(task_description)
            
            cursor.execute("""
                SELECT id, name, description, execution_steps, success_rate
                FROM templates 
                WHERE (embedding <-> %s::vector) < 0.7
                ORDER BY (embedding <-> %s::vector) 
                LIMIT 1
            """, (embedding, embedding))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'execution_steps': row[3],
                    'success_rate': row[4]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Template search failed: {e}")
            return None
        finally:
            cursor.close()

    def store_execution_result(
        self,
        user_id: str,
        task_description: str,
        device_id: str,
        execution_plan: Dict,
        result: Dict
    ) -> str:
        """Store computer execution result"""
        
        cursor = self.pg_conn.cursor()
        
        try:
            execution_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO computer_executions (
                    id, user_id, task_description, device_id,
                    execution_plan, result, success, execution_time, screenshots_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                execution_id, user_id, task_description, device_id,
                json.dumps(execution_plan), json.dumps(result),
                result.get('success', False),
                result.get('execution_time', 0),
                len(result.get('screenshots', []))
            ))
            
            self.pg_conn.commit()
            logger.info(f"✅ Execution result stored: {execution_id}")
            return execution_id
            
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"❌ Execution storage failed: {e}")
            raise
        finally:
            cursor.close()

    def close_connections(self):
        """Close all database connections"""
        try:
            self.pg_conn.close()
            self.redis_conn.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Connection close error: {e}")

# Global instance
_db_manager = None

def get_db_manager() -> AliceDatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = AliceDatabaseManager()
    return _db_manager
