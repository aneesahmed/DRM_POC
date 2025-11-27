import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, JSONResponse
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Load both specific PX secrets from the environment
EZDRM_WIDEVINE_PX = os.getenv("EZDRM_WIDEVINE_PX", "DEFAULT_WV_PX")
EZDRM_PLAYREADY_PX = os.getenv("EZDRM_PLAYREADY_PX", "DEFAULT_PR_PX")

# Define file paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MEDIA_DIR = BASE_DIR / "data"

# --- FASTAPI APP ---
app = FastAPI()

# 1. Mount the /media route to serve video segments
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# 2. Serve the Shaka Player client files (HTML and JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# 3. Endpoint to securely pass both PX values to the client
@app.get("/config.json")
async def get_config():
    """Returns essential configuration data (both PX values) to the client."""
    return JSONResponse(content={
        "EZDRM_WIDEVINE_PX": EZDRM_WIDEVINE_PX,
        "EZDRM_PLAYREADY_PX": EZDRM_PLAYREADY_PX
    })


# 4. Root endpoint to serve the main HTML file
@app.get("/", response_class=HTMLResponse)
async def serve_player():
    """Serves the main Shaka Player HTML page."""
    html_file = STATIC_DIR / "index.html"
    if not html_file.exists():
        return HTMLResponse(content="Error: index.html not found in static folder.", status_code=500)

    with open(html_file, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    print(f"✅ Server starting...")
    print(f"Widevine PX: {EZDRM_WIDEVINE_PX}")
    print(f"PlayReady PX: {EZDRM_PLAYREADY_PX}")
    print(f"Access the player at: http://127.0.0.1:8000/")

    uvicorn.run(app, host="127.0.0.1", port=8000)