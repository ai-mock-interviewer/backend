from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from auth.routes import router as auth_router
from resume.routes import router as resume_router
from config.database import engine, Base

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create tables if they don't exist (development fallback)
    # For production, use: alembic upgrade head
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create tables automatically: {e}")
        print("Please run: alembic upgrade head")
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="AI Mock Interview Backend",
    description="Backend service for AI-powered mock interview platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(resume_router)

@app.get("/")
async def root():
    return {"message": "AI Mock Interview Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
