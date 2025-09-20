import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .database_manager import get_db_manager
from llm import get_llm_response, extract_json_from_response

logger = logging.getLogger(__name__)

class AliceTemplateManager:
    def __init__(self):
        self.db = get_db_manager()
        
    def create_template_from_execution(
        self,
        task_description: str,
        execution_plan: Dict,
        execution_result: Dict,
        created_by: str = None
    ) -> Optional[str]:
        """Create a reusable template from successful execution"""
        
        try:
            # Only create template if execution was successful
            if not execution_result.get('success', False):
                logger.info("❌ Execution failed - no template created")
                return None
            
            # Generate template using Llama 4 Maverick's reasoning
            template_prompt = f"""
            Analyze this successful computer control execution and create a reusable template:
            
            Original Task: "{task_description}"
            
            Execution Plan: {json.dumps(execution_plan, indent=2)}
            
            Execution Result: {json.dumps({
                'success': execution_result['success'],
                'steps_completed': execution_result.get('steps_completed', 0),
                'execution_time': execution_result.get('execution_time', 0)
            }, indent=2)}
            
            Create a JSON template with:
            {{
                "name": "Clear template name",
                "description": "What this template does",
                "trigger_patterns": ["pattern1", "pattern2", "pattern3"],
                "category": "productivity|system|application|automation",
                "difficulty": "easy|medium|hard",
                "estimated_time": 30,
                "execution_steps": {{
                    "steps": [
                        {{
                            "step": 1,
                            "action": "action_name",
                            "description": "Step description",
                            "ducky_script": "DELAY 500\\nGUI r",
                            "verification": "What to verify",
                            "error_handling": "What to do if it fails"
                        }}
                    ],
                    "fallback_steps": [],
                    "requirements": ["requirement1", "requirement2"]
                }},
                "success_indicators": ["indicator1", "indicator2"],
                "common_variations": [
                    {{
                        "condition": "if condition",
                        "modification": "what to change"
                    }}
                ]
            }}
            """
            
            llm_result = get_llm_response(
                template_prompt,
                task_type="reasoning",
                system_prompt="You are Alice's template creation system. Analyze successful executions and create reusable templates."
            )
            
            if llm_result["success"]:
                template_data = extract_json_from_response(llm_result["response"])
                
                if template_data:
                    # Extract template components
                    name = template_data.get('name', f"Template for {task_description[:50]}")
                    description = template_data.get('description', task_description)
                    trigger_patterns = template_data.get('trigger_patterns', [task_description.lower()])
                    execution_steps = template_data.get('execution_steps', execution_plan)
                    
                    # Store in database
                    template_id = self.db.store_template(
                        name=name,
                        description=description,
                        trigger_patterns=trigger_patterns,
                        execution_steps=execution_steps,
                        created_by=created_by
                    )
                    
                    logger.info(f"✅ Template created: {name} (ID: {template_id})")
                    return template_id
                    
        except Exception as e:
            logger.error(f"❌ Template creation failed: {e}")
        
        return None
    
    def find_matching_template(self, task_description: str, similarity_threshold: float = 0.7) -> Optional[Dict]:
        """Find template that matches the task description"""
        
        try:
            # Try database vector search first
            template = self.db.find_matching_template(task_description)
            
            if template:
                logger.info(f"✅ Found matching template: {template['name']}")
                
                # Update usage statistics
                self._update_template_usage(template['id'])
                
                return template
            
            logger.info("ℹ️ No matching template found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Template search failed: {e}")
            return None
    
    def _update_template_usage(self, template_id: str):
        """Update template usage statistics"""
        
        cursor = self.db.pg_conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE templates 
                SET usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (template_id,))
            
            self.db.pg_conn.commit()
            
        except Exception as e:
            self.db.pg_conn.rollback()
            logger.error(f"Template usage update failed: {e}")
        finally:
            cursor.close()
    
    def get_user_templates(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get templates created by user"""
        
        cursor = self.db.pg_conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, description, usage_count, success_rate, 
                       created_at, last_used
                FROM templates 
                WHERE created_by = %s 
                ORDER BY usage_count DESC, created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'usage_count': row[3],
                    'success_rate': row[4],
                    'created_at': row[5].isoformat() if row[5] else None,
                    'last_used': row[6].isoformat() if row[6] else None
                })
            
            return templates
            
        except Exception as e:
            logger.error(f"User templates retrieval failed: {e}")
            return []
        finally:
            cursor.close()
    
    def get_popular_templates(self, limit: int = 5) -> List[Dict]:
        """Get most popular templates"""
        
        cursor = self.db.pg_conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, description, usage_count, success_rate
                FROM templates 
                WHERE usage_count > 0
                ORDER BY (usage_count * success_rate) DESC 
                LIMIT %s
            """, (limit,))
            
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'usage_count': row[3],
                    'success_rate': row[4]
                })
            
            return templates
            
        except Exception as e:
            logger.error(f"Popular templates retrieval failed: {e}")
            return []
        finally:
            cursor.close()
    
    def improve_template(self, template_id: str, execution_result: Dict) -> bool:
        """Improve template based on execution results"""
        
        try:
            cursor = self.db.pg_conn.cursor()
            
            # Get current template
            cursor.execute("""
                SELECT execution_steps, success_rate, usage_count
                FROM templates WHERE id = %s
            """, (template_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            current_steps, current_success_rate, usage_count = row
            success = execution_result.get('success', False)
            
            # Update success rate using weighted average
            new_success_rate = ((current_success_rate * usage_count) + (1.0 if success else 0.0)) / (usage_count + 1)
            
            # If execution failed, analyze what went wrong
            if not success and execution_result.get('errors'):
                improvement_prompt = f"""
                This template execution failed. Analyze the errors and suggest improvements:
                
                Current Steps: {json.dumps(current_steps, indent=2)}
                
                Execution Errors: {execution_result['errors']}
                
                Failed at Step: {execution_result.get('steps_completed', 0)}
                
                Suggest specific improvements to make this template more reliable.
                Focus on adding better delays, error handling, or alternative approaches.
                
                Return JSON with suggested modifications.
                """
                
                llm_result = get_llm_response(
                    improvement_prompt,
                    task_type="reasoning",
                    system_prompt="You are Alice's template improvement system. Analyze failures and suggest fixes."
                )
                
                if llm_result["success"]:
                    # Store improvement suggestions for later review
                    cache_key = f"template_improvements:{template_id}"
                    self.db.redis_conn.setex(cache_key, 86400, llm_result["response"])  # 24 hours
            
            # Update success rate
            cursor.execute("""
                UPDATE templates 
                SET success_rate = %s 
                WHERE id = %s
            """, (new_success_rate, template_id))
            
            self.db.pg_conn.commit()
            
            logger.info(f"✅ Template improved: {template_id} (success rate: {new_success_rate:.2f})")
            return True
            
        except Exception as e:
            self.db.pg_conn.rollback()
            logger.error(f"Template improvement failed: {e}")
            return False
        finally:
            cursor.close()

# Global instance
_template_manager = None

def get_template_manager() -> AliceTemplateManager:
    """Get global template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = AliceTemplateManager()
    return _template_manager
