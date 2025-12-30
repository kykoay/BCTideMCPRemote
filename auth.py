import json 
import logging 

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer 
from fastapi.responses import JSONResponse 
from scalekit import ScalekitClient 
from scalekit.common.scalekit import TokenValidationOptions 
from starlette.middleware.base import BaseHTTPMiddleware  

from config import settings

#Configure logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer() 
# Initiatilize ScaleKit client 
scalekit_client = ScalekitClient(
    env_url=settings.SCALEKIT_ENVIRONMENT_URL,
    client_id=settings.SCALEKIT_CLIENT_ID,
    client_secret=settings.SCALEKIT_CLIENT_SECRET,
)

# Authentication middleware 
class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Authenticate the request using ScaleKit"""
        # TEMP: Bypass auth to test MCP connection (remove after debugging)
        return await call_next(request)
        
        if request.url.path.startswith("/.well-known/"):
        
        try:
            auth_header = request.headers.get("Authorization") 
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
            
            token = auth_header.split(" ")[1]
            
            request_body = await request.body() 
            
            try:
                request_data = json.loads(request_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_data = {}
                
            # Validate the token
            validation_options = TokenValidationOptions(
                audience=[settings.SCALEKIT_AUDIENCE_NAME],
                issuer=settings.SCALEKIT_ISSUER_URL,
            )
            
            is_tool_call = request_data.get("method") == "tools/call"
            
            required_scopes = [] 
            if is_tool_call:
                required_scopes = ["lookup:read"]
                validation_options.required_scopes = required_scopes

            try:
                scalekit_client.validate_token(token, validation_options)
              
            except Exception as e:
                raise HTTPException(status_code=401, detail=str(e))
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "unauthorized" if e.status_code == 401 else "forbidden", "error_description": e.detail},
                headers={
                    "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{settings.SCALEKIT_RESOURCE_METADATA_URL}"'
                }
            )

        return await call_next(request)
