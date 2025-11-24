import base64

from src.tasks.detect_human.detect_human import detectHuman
from src.tasks.classify_fruit.classify_fruit import classifyFruit
from src.tasks.fruit_quality.fruit_quality import fruitQuality
from src.tasks.compression.compression import compress
from src.tasks.encryption.encryption import encrypt

# Test tasks
from src.tasks.addition.addition import addition
from src.tasks.multiplication.multiplication import multiplication
from src.tasks.division.division import division

def decode_binary(binary_in: str) -> bytes:
    return base64.decodebytes(binary_in.encode())

def encode_binary(binary_in: bytes) -> str:
    return base64.encodebytes(binary_in).decode()

def run_task(taskID, parameters: dict):
    result = ""

    match taskID:
        case 0:
            result = detectHuman(decode_binary(parameters["img_bytes"]))
        case 1:
            result = classifyFruit(decode_binary(parameters["img_bytes"]))
        case 2:
            result = fruitQuality(decode_binary(parameters["img_bytes"]))
        case 3:
            result_binary = compress(decode_binary(parameters["data"]))
            result = encode_binary(result_binary)
        case 4:
            result = encrypt(parameters["key"], parameters["plaintext"])

        # Test tasks
        case 100:
            result = addition(parameters["a"], parameters["b"])
        case 101:
            result = multiplication(parameters["a"], parameters["b"])
        case 102:
            result = division(parameters["a"], parameters["b"])

    return result