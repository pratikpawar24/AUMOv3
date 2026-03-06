"""MINIMAL test to verify HF Space Docker works."""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test")

@app.get("/")
async def root():
    return {"status": "alive", "service": "test"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860)
