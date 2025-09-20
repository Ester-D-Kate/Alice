import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from .models import (
    ComputerControlRequest, ComputerControlResponse,
    ScreenshotRequest, ScreenshotResponse,
    DeviceStatusRequest, DeviceStatusResponse
)
from computer_control.control_logic import get_computer_control

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/computer", tags=["Computer Control"])

async def track_processing_time():
    start_time = datetime.now()
    yield start_time

@router.post("/execute", response_model=ComputerControlResponse)
async def execute_computer_task(
    request: ComputerControlRequest,
    start_time: datetime = Depends(track_processing_time)
):
    """
    🖥️ Execute computer control task with AI planning and visual feedback
    """
    
    try:
        logger.info(f"🖥️ Computer control request: '{request.task_description}' on {request.device_id}")
        
        computer_control = get_computer_control()
        
        # Execute the task
        execution_result = await computer_control.execute_computer_task(
            task_description=request.task_description,
            device_id=request.device_id,
            user_id=request.user_id,
            use_template=request.use_template
        )
        
        # Extract template information
        template_info = None
        if execution_result.get("template_used"):
            template_info = {
                "name": execution_result.get("template_used"),
                "template_id": execution_result.get("template_id"),
                "created": execution_result.get("template_created") is not None
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ComputerControlResponse(
            success=execution_result["success"],
            task_description=request.task_description,
            device_id=request.device_id,
            execution_result=execution_result,
            template_info=template_info,
            screenshots_count=len(execution_result.get("screenshots", [])),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Computer control execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshot(
    request: ScreenshotRequest,
    start_time: datetime = Depends(track_processing_time)
):
    """
    📷 Capture screenshot from target device
    """
    
    try:
        logger.info(f"📷 Screenshot request for device: {request.device_id}")
        
        computer_control = get_computer_control()
        
        # Request screenshot
        screenshot_data = await computer_control._request_screenshot(request.device_id)
        
        # Analyze screenshot with AI if available
        analysis = None
        if screenshot_data:
            analysis_result = await computer_control._analyze_screenshot_with_ai(screenshot_data)
            if analysis_result["success"]:
                analysis = analysis_result["analysis"]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ScreenshotResponse(
            success=screenshot_data is not None,
            device_id=request.device_id,
            screenshot_data=screenshot_data,
            analysis=analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Screenshot capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices", response_model=DeviceStatusResponse)
async def get_device_status(request: DeviceStatusRequest = Depends()):
    """
    📱 Get status of all connected devices
    """
    
    try:
        computer_control = get_computer_control()
        
        # Get status for specific device or all devices
        if request.device_id:
            device_status = computer_control.get_device_status(request.device_id)
            devices = [device_status]
        else:
            # For now, return common device IDs - could be enhanced to auto-discover
            common_devices = ["LDrago_windows", "Alice_laptop", "Test_device"]
            devices = [computer_control.get_device_status(device_id) for device_id in common_devices]
        
        return DeviceStatusResponse(
            success=True,
            devices=devices
        )
        
    except Exception as e:
        logger.error(f"❌ Device status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/devices/{device_id}/test")
async def test_device_connection(device_id: str):
    """
    🔧 Test connection to a specific device
    """
    
    try:
        logger.info(f"🔧 Testing connection to device: {device_id}")
        
        computer_control = get_computer_control()
        
        # Simple test - try to get a screenshot
        test_start = datetime.now()
        screenshot = await computer_control._request_screenshot(device_id)
        test_time = (datetime.now() - test_start).total_seconds()
        
        return {
            "success": screenshot is not None,
            "device_id": device_id,
            "connection_test": {
                "screenshot_available": screenshot is not None,
                "response_time": test_time,
                "status": "connected" if screenshot else "disconnected"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Device test failed: {e}")
        return {
            "success": False,
            "device_id": device_id,
            "error": str(e),
            "connection_test": {
                "status": "error"
            }
        }
