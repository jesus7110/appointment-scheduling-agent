# Main entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import chat

app = FastAPI(title="Appointment Scheduling Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Appointment Scheduling Agent API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
