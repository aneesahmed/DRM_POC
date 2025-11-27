import subprocess
import os
import shutil
import base64

# ==========================================
# 1. EZDRM KEYS (from CPIX Response)
# ==========================================
KEY_ID_HEX = "b07b467f9b7948dc9c9a43275ecda95e"
KEY_HEX    = "4c3ade0021c4cbb5aba7acb858648373"  # ← FIXED: Corrected last bytes
IV_HEX     = "b07b467f9b7948dc9c9a43275ecda95e"  # explicitIV from CPIX
EZDRM_PX   = "78C2E8"  # Your PlayReady PX value
GUID_STR   = "b07b467f-9b79-48dc-9c9a-43275ecda95e"

# PSSH Data from CPIX (Base64 from your XML response)
WIDEVINE_PSSH_BASE64 = "AAAAP3Bzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAAB8SELB7Rn+beUjcnJpDJ17NqV4aBWV6ZHJtSPPGiZsG"

# Convert PSSH from Base64 to Hex
def base64_to_hex(b64_string):
    return base64.b64decode(b64_string).hex()

WIDEVINE_PSSH_HEX = base64_to_hex(WIDEVINE_PSSH_BASE64)

# ==========================================
# 2. FOLDER & FILE CONFIGURATION
# ==========================================
INPUT_FILE = r"C:\DRMing\ISHAFC-V1.mp4"
BASE_DIR = r"C:\DRMing\CMAF_Output"

# Clean/Create Directory
if os.path.exists(BASE_DIR):
    shutil.rmtree(BASE_DIR)
os.makedirs(f"{BASE_DIR}/video", exist_ok=True)
os.makedirs(f"{BASE_DIR}/audio", exist_ok=True)

# ==========================================
# 3. CONSTRUCT SHAKA COMMAND
# ==========================================
cmd = [
    "packager",
    
    # --- VIDEO STREAM ---
    (f"in={INPUT_FILE},stream=video,"
     f"init_segment={BASE_DIR}/video/init.mp4,"
     f"segment_template={BASE_DIR}/video/$Number$.m4s,"
     f"playlist_name={BASE_DIR}/video/main.m3u8,"
     f"drm_label=CONTENT"),  # ← Use consistent label
    
    # --- AUDIO STREAM ---
    (f"in={INPUT_FILE},stream=audio,"
     f"init_segment={BASE_DIR}/audio/init.mp4,"
     f"segment_template={BASE_DIR}/audio/$Number$.m4s,"
     f"playlist_name={BASE_DIR}/audio/main.m3u8,"
     f"drm_label=CONTENT"),  # ← Same label for both streams
     
    # --- SEGMENTATION SETTINGS ---
    "--segment_duration", "2",
    
    # --- ENCRYPTION (CBCS for CMAF) ---
    "--enable_raw_key_encryption",
    "--protection_scheme", "cbcs",
    
    # ← FIXED: Use label that matches drm_label above
    "--keys", f"label=CONTENT:key_id={KEY_ID_HEX}:key={KEY_HEX}",
    
    "--iv", IV_HEX,
    
    # ← ADDED: Include PSSH data for Widevine
    "--pssh", WIDEVINE_PSSH_HEX,
    
    "--protection_systems", "Widevine,PlayReady,FairPlay",
    
    # --- DRM HEADERS ---
    "--playready_extra_header_data", 
    f"<LA_URL>https://playready.ezdrm.com/cency/preauth.aspx?pX={EZDRM_PX}</LA_URL>",
    
    # ← FIXED: Full FairPlay license URL
    "--hls_key_uri", f"skd://{GUID_STR}:{KEY_ID_HEX}",
    
    # --- MANIFEST OUTPUTS ---
    "--hls_master_playlist_output", f"{BASE_DIR}/master.m3u8",
    "--mpd_output", f"{BASE_DIR}/manifest.mpd"
]

print(f"Packaging {INPUT_FILE} into '{BASE_DIR}'...")
print(f"\nUsing Key ID: {KEY_ID_HEX}")
print(f"Using Key: {KEY_HEX}")
print(f"PSSH (Hex): {WIDEVINE_PSSH_HEX}\n")

# Run the command
print("-----")
print(cmd)
input("Press Enter to continue...")
try:
    subprocess.run(cmd, check=True)
    print("\n✓ SUCCESS! Packaging complete.")
    print(f"Output files are in: {BASE_DIR}")
    print(f"\nDASH Manifest: {BASE_DIR}/manifest.mpd")
    print(f"HLS Manifest:  {BASE_DIR}/master.m3u8")
except subprocess.CalledProcessError as e:
    print(f"\n✗ ERROR: Shaka Packager failed with code {e.returncode}")
    print("Please check that 'packager' is installed and in your system PATH.")
except FileNotFoundError:
    print("\n✗ ERROR: 'packager' command not found. Is Shaka Packager installed?")