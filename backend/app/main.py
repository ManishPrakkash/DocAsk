from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, documents, analysis
from app.auth import get_current_user
from app.schemas import User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClauseWise Legal Document Analyzer",
    description="A secure, scalable legal document analysis platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    documents.router, 
    prefix="/api/documents", 
    tags=["Documents"],
    dependencies=[Depends(security)]
)
app.include_router(
    analysis.router, 
    prefix="/api/analysis", 
    tags=["Analysis"],
    dependencies=[Depends(security)]
)

@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on startup"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    await close_mongo_connection()

@app.get("/api/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy", "service": "ClauseWise API"}

@app.get("/api/profile", dependencies=[Depends(security)])
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@app.get("/api/user/profile")
async def get_user_profile_alt(current_user: User = Depends(get_current_user)):
    """Alternative user profile endpoint"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@app.get("/api/user/profile/public")
async def get_public_profile():
    """Public profile endpoint for testing"""
    return {
        "message": "Profile endpoint is working",
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)