import os
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _encrypt(key_b64: bytes, plaintext: bytes) -> bytes:
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # store nonce + ciphertext together
    return base64.b64encode(nonce + ciphertext)

def encrypt(data: bytes) -> bytes:
    params = json.loads(data.decode())
    return _encrypt(params["key"].encode(), params["plaintext"].encode())

def _decrypt(key_b64: bytes, ciphertext_b64: bytes) -> bytes:
    key = base64.b64decode(key_b64)
    data = base64.b64decode(ciphertext_b64)

    nonce = data[:12]
    ct = data[12:]

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext

def decrypt(data: bytes) -> bytes:
    params = json.loads(data.decode())
    return _decrypt(params["key"].encode(), params["ciphertext"].encode())