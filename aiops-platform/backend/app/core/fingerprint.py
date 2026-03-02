import hashlib

def generate_fingerprint(service: str, api: str, message: str):
    raw = f"{service}|{api}|{message}"
    return hashlib.sha256(raw.encode()).hexdigest()