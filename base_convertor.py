import base64
import binascii

# Extracted from XML:
KID_GUID = "b07b467f-9b79-48dc-9c9a-43275ecda95e"
BASE64_KEY = "TDreACHEy7Wrp6y4WOSD3A=="

# Conversion:
KID_HEX = KID_GUID.replace('-', '')
CONTENT_KEY_HEX = binascii.hexlify(base64.b64decode(BASE64_KEY)).decode('utf-8')

print(f"Key ID (HEX): {KID_HEX}")
print(f"Content Key (HEX): {CONTENT_KEY_HEX}")