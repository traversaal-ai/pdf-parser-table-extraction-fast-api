from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Health"])
 
@router.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"} 