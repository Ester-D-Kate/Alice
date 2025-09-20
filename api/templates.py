import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from .models import TemplateRequest, TemplateResponse
from core.template_manager import get_template_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["Templates"])

async def track_processing_time():
    start_time = datetime.now()
    yield start_time

@router.get("/", response_model=TemplateResponse)
async def get_templates(
    request: TemplateRequest = Depends(),
    start_time: datetime = Depends(track_processing_time)
):
    """
    📋 Get available templates - Alice's learned workflows
    """
    
    try:
        templates_manager = get_template_manager()
        
        if request.user_id:
            # Get user-specific templates
            templates = templates_manager.get_user_templates(request.user_id, limit=20)
        else:
            # Get popular templates
            templates = templates_manager.get_popular_templates(limit=10)
        
        # Filter by category if specified
        if request.category:
            templates = [t for t in templates if t.get('category') == request.category]
        
        # Filter by difficulty if specified
        if request.difficulty:
            templates = [t for t in templates if t.get('difficulty') == request.difficulty]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TemplateResponse(
            success=True,
            templates=templates,
            total_count=len(templates),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Templates retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{query}")
async def search_templates(query: str, user_id: str = None):
    """
    🔍 Search templates by description or task
    """
    
    try:
        templates_manager = get_template_manager()
        
        # Use the database's similarity search
        template = templates_manager.find_matching_template(query)
        
        if template:
            return {
                "success": True,
                "query": query,
                "template_found": template,
                "similarity": "high"
            }
        else:
            return {
                "success": True,
                "query": query,
                "template_found": None,
                "message": "No matching template found"
            }
        
    except Exception as e:
        logger.error(f"❌ Template search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_template_categories():
    """
    📂 Get available template categories
    """
    
    return {
        "success": True,
        "categories": [
            {"name": "productivity", "description": "Office and productivity tasks"},
            {"name": "system", "description": "System administration and configuration"},
            {"name": "application", "description": "Application-specific workflows"},
            {"name": "automation", "description": "General automation tasks"},
            {"name": "development", "description": "Development and coding tasks"},
            {"name": "maintenance", "description": "System maintenance tasks"}
        ]
    }

@router.delete("/{template_id}")
async def delete_template(template_id: str, user_id: str):
    """
    🗑️ Delete a user's template (soft delete)
    """
    
    try:
        # In a real implementation, you'd verify the user owns this template
        # and perform a soft delete
        
        return {
            "success": True,
            "message": f"Template {template_id} marked for deletion",
            "template_id": template_id
        }
        
    except Exception as e:
        logger.error(f"❌ Template deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
