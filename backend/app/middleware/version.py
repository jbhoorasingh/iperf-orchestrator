from fastapi import Request, HTTPException, status
from app.config import settings


async def version_middleware(request: Request, call_next):
    """Middleware to enforce API version header"""
    # Skip version check for docs, health, and auth endpoints
    skip_paths = ["/healthz", "/docs", "/redoc", "/openapi.json", "/v1/auth/login"]
    if request.url.path in skip_paths:
        response = await call_next(request)
        return response
    
    # Check for X-API-Version header
    api_version = request.headers.get("X-API-Version")
    
    if not api_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "missing_version_header",
                "message": "X-API-Version header is required",
                "details": {"required_version": settings.api_version}
            }
        )
    
    try:
        version_num = int(api_version)
        if version_num != settings.api_version:
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail={
                    "error": "unsupported_version",
                    "message": "Unsupported API version",
                    "details": {"min": settings.api_version, "max": settings.api_version}
                }
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_version_format",
                "message": "X-API-Version must be a number",
                "details": {"provided": api_version}
            }
        )
    
    response = await call_next(request)
    response.headers["X-API-Version"] = str(settings.api_version)
    return response
