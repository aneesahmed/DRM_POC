import httpx
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PROXY_URL = "http://localhost:8000/license-proxy"

# --- Test Data ---
# 1. Simulates the small 2-byte or 60-byte Certificate Request.
# A small body should usually be rejected by EZDRM.
CERT_CHALLENGE = b"0x02"

# 2. Simulates a large License Challenge (real challenges are > 2000 bytes).
# This is what the player sends when it needs the key.
LICENSE_CHALLENGE = os.urandom(2500)


async def run_test(name, challenge_body):
    """Sends a specific challenge to the local proxy and reports the result."""
    print(f"\n--- Running Test: {name} ---")
    print(f"Request Size: {len(challenge_body)} bytes")

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                PROXY_URL,
                content=challenge_body,
                # Ensure we send the expected binary content type
                headers={"Content-Type": "application/octet-stream"}
            )

            print(f"Response Status: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")

            if response.status_code in [200, 201]:
                # If length is small (Test 1), 200 OK means EZDRM sent an error message.
                # If length is large (Test 2), 200 OK means SUCCESS (Key received).
                if name == "Certificate Test" and len(response.content) < 500:
                    print("Result: ❌ EZDRM returned 200 OK, but likely sent an error MESSAGE (text).")
                    print("   Content Preview:", response.text.strip()[:100] + "...")
                elif name == "License Test":
                    print("Result: ✅ SUCCESS! EZDRM responded with a large binary payload (key).")

            elif response.status_code in [400, 500]:
                print(f"Result: ⚠️ FAILED. EZDRM rejected the request.")
                print("   Error Hint:", response.text.strip()[:100] + "...")

        except httpx.ConnectError:
            print("Result: ❌ CONNECTION ERROR. Ensure main.py is running on port 8000.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


async def main():
    await run_test("Certificate Test", CERT_CHALLENGE)
    await run_test("License Test", LICENSE_CHALLENGE)
    print("\n--- Diagnostics Complete ---")


if __name__ == "__main__":
    asyncio.run(main())