import base64
from lib.scheduler import Tasks

from src.tasks.detect_human.detect_human import detectHuman
from src.tasks.classify_fruit.classify_fruit import classifyFruit
from src.tasks.fruit_quality.fruit_quality import fruitQuality
from src.tasks.compression.compression import compress, decompress
from src.tasks.encryption.encryption import encrypt, decrypt

# Test tasks
from src.tasks.addition.addition import addition
from src.tasks.multiplication.multiplication import multiplication
from src.tasks.division.division import division

def decode_binary(binary_in: str) -> bytes:
    b64_bytes = binary_in.encode()
    raw_bytes = base64.decodebytes(b64_bytes)
    return raw_bytes

def encode_binary(binary_in: bytes) -> str:
    b64_bytes = base64.encodebytes(binary_in)
    b64_string = b64_bytes.decode()
    return b64_string

def run_task(taskID: int, data: bytes) -> bytes:
    result = ""

    match taskID:
        case Tasks.DETECT_HUMAN:
            result = detectHuman(data)
        case Tasks.CLASSIFY_FRUIT:
            result = classifyFruit(data)
        case Tasks.FRUIT_QUALITY:
            result = fruitQuality(data)
        case Tasks.COMPRESSION:
            result = compress(data)
        case Tasks.DECOMPRESSION:
            result = decompress(data)
        case Tasks.ENCRYPTION:
            result = encrypt(data)
        case Tasks.DECRYPTION:
            result = decrypt(data)

        # Test tasks
        case Tasks.ADDITION:
            result = addition(data)
        case Tasks.MULTIPLICATION:
            result = multiplication(data)
        case Tasks.DIVISION:
            result = division(data)

    return result