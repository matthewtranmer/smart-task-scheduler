import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(key_b64: str, plaintext: str) -> str:
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # store nonce + ciphertext together
    return base64.b64encode(nonce + ct).decode("utf-8")

def decrypt(key_b64: str, token_b64: str) -> str:
    key = base64.b64decode(key_b64)
    data = base64.b64decode(token_b64)

    nonce = data[:12]
    ct = data[12:]

    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt.decode("utf-8")