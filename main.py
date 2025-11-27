import os
import uvicorn
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

# --- Configuration ---
# The Base URL for your AWS CloudFront distribution
CDN_BASE_URL = "https://d33lpnn61x8wuf.cloudfront.net/media/course/videos/the-fundamentals-laning-course/DRMTEST/"
# ---------------------

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


# 3. THE CDN PROXY ROUTE
# This intercepts requests for files (dash.mpd, .m4s segments) and forwards them to CloudFront
@app.get("/stream/{path:path}")
async def cdn_proxy(path: str):
    full_cdn_url = f"{CDN_BASE_URL}{path}"
    print(f"🌍 CDN Proxy Request: Forwarding to {full_cdn_url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Stream the request to avoid loading large video files into memory
            req = client.build_request("GET", full_cdn_url)
            r = await client.send(req, stream=True)

            # If the CDN returns a 404 or 403, raise it immediately
            if r.status_code >= 400:
                print(f"❌ CDN Error {r.status_code}: {full_cdn_url}")
                return Response(f"CDN Error: {r.status_code}", status_code=r.status_code)

            # Stream the content back to the browser
            return StreamingResponse(
                r.aiter_bytes(),
                status_code=r.status_code,
                headers={
                    "Content-Type": r.headers.get("Content-Type", "application/octet-stream"),
                    "Content-Length": r.headers.get("Content-Length"),
                }
            )

        except Exception as e:
            print(f"❌ CDN Proxy Connection Failed: {e}")
            return Response(f"Proxy Error: {str(e)}", status_code=500)


# 4. THE LICENSE PROXY ROUTE (Logging Errors)
@app.post("/license-proxy")
async def license_proxy(request: Request):
    if not WIDEVINE_PX:
        print("❌ Error: EZDRM_WIDEVINE_PX is missing from .env file")
        return Response("Server Configuration Error: Missing PX", status_code=500)

    client_body = await request.body()
    print(f"✅ Receiving License Request. Size: {len(client_body)} bytes. Forwarding to EZDRM...")

    # Construct the EZDRM URL
    ezdrm_url = f"https://widevine-dash.ezdrm.com/proxy?pX={WIDEVINE_PX}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Content-Type": "application/octet-stream",
            "User-Agent": "FastAPI Local Proxy",
        }

        try:
            ezdrm_response = await client.post(
                ezdrm_url,
                content=client_body,
                headers=headers
            )

            if ezdrm_response.status_code != 200:
                print(f"🚨 EZDRM Error {ezdrm_response.status_code}")
                print(f"   Response: {ezdrm_response.text[:200]}")
            else:
                print(f"   ⬅️ EZDRM Success (200 OK)")

            return Response(
                content=ezdrm_response.content,
                status_code=ezdrm_response.status_code,
                media_type="application/octet-stream"
            )
        except Exception as e:
            print(f"❌ License Proxy Error: {e}")
            return Response(f"Proxy Error: {str(e)}", status_code=500)


# 5. Serve the Player Interface
@app.get("/")
async def get_html():
    try:
        with open("index.html", "r", encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return Response("Error: index.html not found", status_code=404)


# --- MAIN EXECUTION BLOCK (HTTPS ENABLED) ---
if __name__ == "__main__":
    print("----------------------------------------------------------------")
    print(f"CDN Target: {CDN_BASE_URL}")

    # Check for SSL Certificates
    if os.path.exists("key.pem") and os.path.exists("cert.pem"):
        print(f"✅ SSL Certificates found. Starting Secure Server.")
        print(f"👉 Local Access:   https://localhost:8000")
        print(f"👉 Network Access: https://192.168.18.17:8000")
        print("----------------------------------------------------------------")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            ssl_keyfile="key.pem",
            ssl_certfile="cert.pem"
        )
    else:
        print("----------------------------------------------------------------")
        print("❌ SSL CERTIFICATES MISSING ('key.pem' or 'cert.pem')")
        print("   DRM on Firefox/Network requires HTTPS.")
        print("   Run this command in terminal to generate them:")
        print("   > mkcert localhost 192.168.18.17 0.0.0.0")
        print("----------------------------------------------------------------")
        # Fallback to HTTP if user really wants, or just exit.
        # Here we exit to enforce the fix.