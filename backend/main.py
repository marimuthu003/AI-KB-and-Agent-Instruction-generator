import os
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from crawler_engine.routes import router as crawler_router

app = FastAPI()
app.include_router(crawler_router)

# Serve frontend assets
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
