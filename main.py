import contextlib
import uvicorn  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import AuthenticationMiddleware
from config import settings
from bctides import mcp as bc_tides_mcp_server
import json

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with bc_tides_mcp_server.session_manager.run():
        yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata():
    """"
    OAuth 2.0 Protected Resource Metadata endpoint for MCP client discovery.
    Required by the MCP specification for authorization server discovery.
    """
    response = json.loads(settings.METADATA_JSON_RESPONSE)
    return response 

# Mount the server
mcp_server = bc_tides_mcp_server.streamable_http_app() 
app.add_middleware(AuthenticationMiddleware)
app.mount("/", mcp_server)

def main():
    """Main entry point for the application"""
    uvicorn.run(app, host="localhost", port=settings.PORT, log_level="debug")

if __name__ == "__main__":
    main()