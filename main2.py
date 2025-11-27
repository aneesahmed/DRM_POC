import os
import uvicorn
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# 1. Load Environment Variables
load_dotenv()
WIDEVINE_PX = os.getenv("EZDRM_WIDEVINE_PX")
PLAYREADY_PX = os.getenv("EZDRM_PLAYREADY_PX")

app = FastAPI()

# 2. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount the Data Folder
app.mount("/stream", StaticFiles(directory="data"), name="data")


# 4. THE PROXY ROUTE (Logging Errors)
@app.post("/license-proxy")
async def license_proxy(request: Request):
    if not WIDEVINE_PX:
        print("❌ Error: EZDRM_WIDEVINE_PX is missing from .env file")
        return Response("Server Configuration Error: Missing PX", status_code=500)

    client_body = await request.body()
    body_length = len(client_body)

    print(f"✅ Receiving request. Size: {body_length} bytes. Forwarding to EZDRM...")

    # Construct the EZDRM URL
    ezdrm_url = f"https://widevine-dash.ezdrm.com/proxy?pX={WIDEVINE_PX}"

    # Use a client with a timeout
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Content-Type": "application/octet-stream",
            "User-Agent": "FastAPI Local Proxy",
        }

        try:
            # Forward the request to EZDRM
            ezdrm_response = await client.post(
                ezdrm_url,
                content=client_body,
                headers=headers
            )

            # --- DIAGNOSTIC LOGGING ---
            if ezdrm_response.status_code == 500:
                print("\n🚨 EZDRM 500 ERROR RECEIVED 🚨")
                print(f"Content Preview (Internal EZDRM Error):\n{ezdrm_response.text[:500]}...")
            # --------------------------

            print(f"   ⬅️ EZDRM Response Status: {ezdrm_response.status_code}")

            # Return the response as before
            return Response(
                content=ezdrm_response.content,
                status_code=ezdrm_response.status_code,
                media_type="application/octet-stream"
            )
        except Exception as e:
            print(f"❌ Proxy Error (httpx failed to connect or time out): {e}")
            return Response(f"Proxy Error: {str(e)}", status_code=500)


# 5. Serve the Player Interface (FIXED: Added encoding='utf-8')
@app.get("/")
async def get_html():
    try:
        # FIX APPLIED HERE: Specify encoding='utf-8' to prevent UnicodeDecodeError
        with open("index.html", "r", encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return Response("Error: index.html not found", status_code=404)


if __name__ == "__main__":
    print("----------------------------------------------------------------")
    print(f"Server starting at http://localhost:8000")
    print("WARNING: Blocking is disabled. Look for 500 error details in the terminal.")
    print("----------------------------------------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=8000)