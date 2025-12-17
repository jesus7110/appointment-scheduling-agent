import os
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

load_dotenv()  #from current directory

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "8100"))
    uvicorn.run(app, host="0.0.0.0", port=port)
