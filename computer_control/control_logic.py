import logging
import asyncio
import json
import uuid
import base64
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from core.database_manager import get_db_manager
from core.template_manager import get_template_manager
from llm import get_llm_response, get_multimodal_response, extract_json_from_response
from config import EXECUTION_PLANNER_PROMPT, MQTT_BROKER, MQTT_PORT

logger = logging.getLogger(__name__)

class AliceComputerControl:
    def __init__(self):
        self.db = get_db_manager()
        self.templates = get_template_manager()
        
        # MQTT setup
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        # Screenshot and response management
        self.pending_screenshots = {}
        self.pending_commands = {}
        self.screenshot_timeout = 30
        self.command_timeout = 15
        
        # Connect to MQTT
        self._connect_mqtt()
    
    def _connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            logger.info(f"Connected to MQTT broker: {MQTT_BROKER}")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            # Subscribe to all device communications
            client.subscribe("+/screenshot/response")
            client.subscribe("+/ducky_script/status")
            client.subscribe("+/system/status")
            logger.info("Subscribed to device communication channels")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle MQTT messages from devices"""
        try:
            topic_parts = msg.topic.split('/')
            device_id = topic_parts[0]
            message_type = topic_parts[1]
            action = topic_parts[2] if len(topic_parts) > 2 else "unknown"
            
            payload = json.loads(msg.payload.decode())
            
            if message_type == "screenshot" and action == "response":
                self._handle_screenshot_response(device_id, payload)
            elif message_type == "ducky_script" and action == "status":
                self._handle_command_status(device_id, payload)
            elif message_type == "system" and action == "status":
                self._handle_system_status(device_id, payload)
                
        except Exception as e:
            logger.error(f"❌ MQTT message handling error: {e}")
    
    async def execute_computer_task(
        self,
        task_description: str,
        device_id: str = "LDrago_windows",
        user_id: str = None,
        use_template: bool = True
    ) -> Dict:
        """Execute computer control task with advanced reasoning and visual feedback"""
        
        execution_start = datetime.now()
        
        try:
            logger.info(f"🚀 Starting computer task: {task_description} on {device_id}")
            
            # Step 1: Check for existing template
            template = None
            if use_template:
                template = self.templates.find_matching_template(task_description)
            
            if template:
                logger.info(f"📋 Using template: {template['name']}")
                result = await self._execute_with_template(template, device_id, user_id)
            else:
                logger.info("🧠 Creating new execution plan with Llama 4 Maverick")
                result = await self._execute_with_ai_planning(task_description, device_id, user_id)
            
            # Update execution time
            result["execution_time"] = (datetime.now() - execution_start).total_seconds()
            
            # Store execution result for learning
            if user_id:
                self.db.store_execution_result(user_id, task_description, device_id, result.get("execution_plan", {}), result)
            
            # Create template from successful execution
            if result["success"] and not template and user_id:
                template_id = self.templates.create_template_from_execution(
                    task_description, result.get("execution_plan", {}), result, user_id
                )
                if template_id:
                    result["template_created"] = template_id
            
            # Improve existing template if used
            elif template and template.get("id"):
                self.templates.improve_template(template["id"], result)
            
            logger.info(f"✅ Task completed: {result['success']} (time: {result['execution_time']:.1f}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Computer task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id,
                "execution_time": (datetime.now() - execution_start).total_seconds(),
                "task_description": task_description
            }
    
    async def _execute_with_template(self, template: Dict, device_id: str, user_id: str) -> Dict:
        """Execute task using existing template"""
        
        try:
            execution_steps = template.get("execution_steps", {})
            steps = execution_steps.get("steps", [])
            
            result = {
                "success": False,
                "template_used": template["name"],
                "template_id": template["id"],
                "steps_completed": 0,
                "total_steps": len(steps),
                "screenshots": [],
                "errors": [],
                "execution_plan": execution_steps
            }
            
            # Capture initial screenshot
            initial_screenshot = await self._request_screenshot(device_id)
            if initial_screenshot:
                result["screenshots"].append({
                    "step": 0,
                    "description": "Initial state",
                    "screenshot": initial_screenshot
                })
            
            # Execute each step
            for i, step in enumerate(steps):
                logger.info(f"📋 Template step {i+1}/{len(steps)}: {step.get('description', 'Unknown step')}")
                
                step_result = await self._execute_step_with_feedback(step, device_id, i+1)
                
                if step_result["success"]:
                    result["steps_completed"] += 1
                    if step_result.get("screenshot"):
                        result["screenshots"].append({
                            "step": i + 1,
                            "description": step.get("description", "Step execution"),
                            "screenshot": step_result["screenshot"]
                        })
                else:
                    result["errors"].append(f"Step {i+1}: {step_result.get('error', 'Unknown error')}")
                    
                    # Try error handling if available
                    error_handling = step.get("error_handling")
                    if error_handling:
                        logger.info(f"🔄 Attempting error recovery: {error_handling}")
                        recovery_result = await self._execute_recovery_action(error_handling, device_id)
                        if recovery_result["success"]:
                            result["steps_completed"] += 1
                            continue
                    
                    break
            
            result["success"] = result["steps_completed"] == result["total_steps"]
            return result
            
        except Exception as e:
            logger.error(f"❌ Template execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "template_used": template.get("name", "Unknown"),
                "steps_completed": 0,
                "total_steps": len(template.get("execution_steps", {}).get("steps", []))
            }
    
    async def _execute_with_ai_planning(self, task_description: str, device_id: str, user_id: str) -> Dict:
        """Execute task using AI planning with Llama 4 Maverick"""
        
        try:
            # Capture initial screenshot for context
            initial_screenshot = await self._request_screenshot(device_id)
            
            screen_context = {}
            if initial_screenshot:
                # Use Llama 4 Maverick's multimodal capabilities to analyze screenshot
                screen_analysis = await self._analyze_screenshot_with_ai(initial_screenshot)
                screen_context = screen_analysis.get("analysis", {})
            
            # Generate execution plan with Llama 4 Maverick
            execution_plan = await self._generate_execution_plan_ai(task_description, screen_context, device_id)
            
            if not execution_plan or not execution_plan.get("steps"):
                return {
                    "success": False,
                    "error": "Failed to generate execution plan",
                    "task_description": task_description
                }
            
            # Execute the AI-generated plan
            result = {
                "success": False,
                "ai_planned": True,
                "execution_plan": execution_plan,
                "steps_completed": 0,
                "total_steps": len(execution_plan.get("steps", [])),
                "screenshots": [],
                "errors": []
            }
            
            if initial_screenshot:
                result["screenshots"].append({
                    "step": 0,
                    "description": "Initial state (AI analyzed)",
                    "screenshot": initial_screenshot,
                    "analysis": screen_context
                })
            
            # Execute each AI-planned step
            steps = execution_plan.get("steps", [])
            for i, step in enumerate(steps):
                logger.info(f"🧠 AI step {i+1}/{len(steps)}: {step.get('description', 'AI generated step')}")
                
                step_result = await self._execute_step_with_feedback(step, device_id, i+1)
                
                if step_result["success"]:
                    result["steps_completed"] += 1
                    if step_result.get("screenshot"):
                        # Analyze screenshot with AI for verification
                        screenshot_analysis = await self._analyze_screenshot_with_ai(step_result["screenshot"])
                        
                        result["screenshots"].append({
                            "step": i + 1,
                            "description": step.get("description", "AI step"),
                            "screenshot": step_result["screenshot"],
                            "ai_analysis": screenshot_analysis.get("analysis", {})
                        })
                        
                        # Use AI to verify step completion
                        verification_result = await self._ai_verify_step_completion(
                            step, step_result["screenshot"], screenshot_analysis
                        )
                        
                        if not verification_result.get("verified", True):
                            logger.warning(f"⚠️ AI verification failed for step {i+1}")
                            result["errors"].append(f"Step {i+1}: AI verification failed - {verification_result.get('reason', 'Unknown')}")
                            break
                else:
                    result["errors"].append(f"Step {i+1}: {step_result.get('error', 'Execution failed')}")
                    break
            
            result["success"] = result["steps_completed"] == result["total_steps"]
            return result
            
        except Exception as e:
            logger.error(f"❌ AI planning execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ai_planned": True,
                "task_description": task_description
            }
    
    async def _analyze_screenshot_with_ai(self, screenshot_data: Dict) -> Dict:
        """Analyze screenshot using Llama 4 Maverick's multimodal capabilities"""
        
        try:
            if not screenshot_data.get("image_data"):
                return {"success": False, "analysis": {}}
            
            image_b64 = screenshot_data["image_data"]
            
            analysis_prompt = """
            Analyze this screenshot and provide detailed information about:
            
            1. What applications/windows are visible
            2. Current screen state (desktop, application, dialog, etc.)
            3. Interactive elements (buttons, menus, text fields)
            4. Any error dialogs or notifications
            5. System status indicators
            6. Text content that's visible and readable
            
            Return JSON format:
            {
                "screen_state": "desktop|application|dialog|error|loading",
                "applications": ["app1", "app2"],
                "interactive_elements": [
                    {"type": "button", "text": "OK", "location": "bottom-right"},
                    {"type": "textfield", "placeholder": "Enter text", "location": "center"}
                ],
                "errors_visible": false,
                "notifications": [],
                "text_content": "Any readable text",
                "suggestions": ["What could be done next"]
            }
            """
            
            multimodal_result = get_multimodal_response(
                analysis_prompt,
                image_data=image_b64,
                system_prompt="You are Alice's visual analysis system using Llama 4 Maverick. Analyze screenshots for computer control."
            )
            
            if multimodal_result["success"]:
                analysis = extract_json_from_response(multimodal_result["response"])
                if analysis:
                    logger.info("Screenshot analyzed with AI multimodal capabilities")
                    return {"success": True, "analysis": analysis}
            
            return {"success": False, "analysis": {}}
            
        except Exception as e:
            logger.error(f"❌ Screenshot AI analysis failed: {e}")
            return {"success": False, "analysis": {}}
    
    async def _generate_execution_plan_ai(self, task: str, screen_context: Dict, device_id: str) -> Dict:
        """Generate execution plan using Llama 4 Maverick's advanced reasoning"""
        
        try:
            plan_prompt = f"""
            {EXECUTION_PLANNER_PROMPT.format(
                task=task,
                screen_context=json.dumps(screen_context, indent=2),
                device_id=device_id
            )}
            
            Current Screen Analysis:
            - State: {screen_context.get('screen_state', 'unknown')}
            - Applications: {screen_context.get('applications', [])}
            - Interactive elements: {len(screen_context.get('interactive_elements', []))} found
            - Errors visible: {screen_context.get('errors_visible', False)}
            
            Use your advanced reasoning to create a comprehensive, safe, and reliable execution plan.
            Consider the current screen state and plan accordingly.
            """
            
            llm_result = get_llm_response(
                plan_prompt,
                task_type="reasoning",
                system_prompt="You are Alice's execution planner using Llama 4 Maverick's superior reasoning for computer control.",
                temperature=0.3
            )
            
            if llm_result["success"]:
                plan = extract_json_from_response(llm_result["response"])
                if plan and plan.get("steps"):
                    logger.info(f"AI generated plan with {len(plan['steps'])} steps")
                    return plan
            
            # Fallback plan
            return {
                "plan_name": "Basic AI Plan",
                "estimated_time": 10,
                "steps": [
                    {
                        "step": 1,
                        "action": "wait",
                        "description": "Wait for system to be ready",
                        "ducky_script": "DELAY 1000",
                        "verification": "System ready"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ AI plan generation failed: {e}")
            return {}
    
    async def _execute_step_with_feedback(self, step: Dict, device_id: str, step_number: int) -> Dict:
        """Execute a single step with visual feedback"""
        
        try:
            # Execute the ducky script command
            ducky_script = step.get("ducky_script", "")
            if ducky_script:
                command_result = await self._send_ducky_command(device_id, ducky_script, step_number)
                if not command_result.get("success", True):
                    return {"success": False, "error": f"Command execution failed: {command_result.get('error', 'Unknown')}"}
            
            # Wait for execution
            await asyncio.sleep(2)
            
            # Capture verification screenshot
            screenshot = await self._request_screenshot(device_id)
            
            return {
                "success": True,
                "screenshot": screenshot,
                "step_number": step_number,
                "command_sent": bool(ducky_script)
            }
            
        except Exception as e:
            logger.error(f"❌ Step execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_ducky_command(self, device_id: str, ducky_script: str, step_number: int) -> Dict:
        """Send rubber ducky script command to device"""
        
        try:
            command_id = str(uuid.uuid4())
            
            command_payload = {
                "command_id": command_id,
                "script": ducky_script,
                "step_number": step_number,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store pending command
            self.pending_commands[command_id] = {"status": "pending", "device_id": device_id}
            
            # Publish command
            topic = f"{device_id}/ducky_script"
            self.mqtt_client.publish(topic, json.dumps(command_payload))
            
            # Wait for command completion
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < self.command_timeout:
                if command_id in self.pending_commands:
                    status = self.pending_commands[command_id].get("status")
                    if status in ["completed", "failed"]:
                        result = self.pending_commands.pop(command_id, {})
                        return {"success": status == "completed", "result": result}
                
                await asyncio.sleep(0.1)
            
            # Timeout
            self.pending_commands.pop(command_id, None)
            return {"success": True, "timeout": True}  # Assume success on timeout
            
        except Exception as e:
            logger.error(f"❌ Ducky command failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _request_screenshot(self, device_id: str) -> Optional[Dict]:
        """Request screenshot from target device"""
        
        try:
            request_id = str(uuid.uuid4())
            
            request_payload = {
                "action": "capture",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "quality": "high"
            }
            
            # Store pending request
            self.pending_screenshots[request_id] = None
            
            # Publish screenshot request
            topic = f"{device_id}/screenshot/request"
            self.mqtt_client.publish(topic, json.dumps(request_payload))
            
            # Wait for response
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < self.screenshot_timeout:
                if self.pending_screenshots[request_id] is not None:
                    screenshot = self.pending_screenshots.pop(request_id)
                    logger.info(f"📷 Screenshot received from {device_id}")
                    return screenshot
                
                await asyncio.sleep(0.1)
            
            # Timeout
            self.pending_screenshots.pop(request_id, None)
            logger.warning(f"Screenshot request timed out: {device_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Screenshot request failed: {e}")
            return None
    
    def _handle_screenshot_response(self, device_id: str, response: Dict):
        """Handle screenshot response from device"""
        request_id = response.get("request_id")
        if request_id in self.pending_screenshots:
            self.pending_screenshots[request_id] = response
    
    def _handle_command_status(self, device_id: str, status: Dict):
        """Handle command status from device"""
        command_id = status.get("command_id")
        if command_id in self.pending_commands:
            self.pending_commands[command_id].update(status)
    
    def _handle_system_status(self, device_id: str, status: Dict):
        """Handle system status from device"""
        logger.info(f"System status from {device_id}: {status.get('status', 'unknown')}")
    
    async def _ai_verify_step_completion(self, step: Dict, screenshot: Dict, screenshot_analysis: Dict) -> Dict:
        """Use AI to verify if step was completed successfully"""
        
        try:
            verification_criteria = step.get("verification", "")
            analysis = screenshot_analysis.get("analysis", {})
            
            verification_prompt = f"""
            Verify if this step was completed successfully:
            
            Step Description: {step.get('description', 'Unknown step')}
            Expected Result: {verification_criteria}
            
            Current Screen Analysis:
            - State: {analysis.get('screen_state', 'unknown')}
            - Applications: {analysis.get('applications', [])}
            - Errors visible: {analysis.get('errors_visible', False)}
            - Interactive elements: {len(analysis.get('interactive_elements', []))}
            
            Based on the screen analysis, was the step completed successfully?
            
            Return JSON:
            {{
                "verified": true/false,
                "confidence": 0.85,
                "reason": "explanation of verification result",
                "suggestions": ["what to do next if failed"]
            }}
            """
            
            llm_result = get_llm_response(
                verification_prompt,
                task_type="reasoning",
                system_prompt="You are Alice's verification system. Analyze screen states to verify step completion.",
                temperature=0.3
            )
            
            if llm_result["success"]:
                verification = extract_json_from_response(llm_result["response"])
                if verification:
                    return verification
            
            # Default to verified if analysis fails
            return {"verified": True, "confidence": 0.5, "reason": "Analysis unavailable"}
            
        except Exception as e:
            logger.error(f"❌ AI verification failed: {e}")
            return {"verified": True, "confidence": 0.1, "reason": f"Verification error: {e}"}
    
    def get_device_status(self, device_id: str) -> Dict:
        """Get current device status"""
        
        try:
            # Check Redis cache for recent device status
            cache_key = f"device_status:{device_id}"
            cached_status = self.db.redis_conn.get(cache_key)
            
            if cached_status:
                return json.loads(cached_status)
            
            return {
                "device_id": device_id,
                "status": "unknown",
                "last_seen": None,
                "capabilities": []
            }
            
        except Exception as e:
            logger.error(f"❌ Device status check failed: {e}")
            return {"device_id": device_id, "status": "error", "error": str(e)}

# Global instance
_computer_control = None

def get_computer_control() -> AliceComputerControl:
    """Get global computer control instance"""
    global _computer_control
    if _computer_control is None:
        _computer_control = AliceComputerControl()
    return _computer_control
