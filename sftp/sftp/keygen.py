import secrets
import base64

# Generate a 32-byte random key
random_key = secrets.token_bytes(32)

# Encode it as base64
encoded_key = base64.urlsafe_b64encode(random_key).decode()

print(f"Your secure random key: {encoded_key}")
