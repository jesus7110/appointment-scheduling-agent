import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from api.websocket import router as websocket_router

# Create FastAPI app
app = FastAPI(
    title="Appointment Scheduling API",
    description="API for medical appointment scheduling with AI assistant",
    version="1.0.0"
)

# Configure CORS (allow frontend to communicate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Common React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Appointment Scheduling API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Main health check endpoint."""
    return {
        "status": "ok",
        "service": "appointment-scheduling-api"
    }


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "8100"))
    print(f"🚀 Starting server on http://0.0.0.0:{port}")
    print(f"📚 API docs available at http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
