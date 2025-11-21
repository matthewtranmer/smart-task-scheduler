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

def decode_image(image_in: str) -> bytes:
    return base64.decodebytes(image_in.encode())

def run_task(taskID, parameters: dict):
    result = ""

    match taskID:
        case 0:
            result = detectHuman(decode_image(parameters["img_bytes"]))
        case 1:
            result = classifyFruit(decode_image(parameters["img_bytes"]))
        case 2:
            result = fruitQuality(decode_image(parameters["img_bytes"]))
        case 3:
            result = compress(parameters["data"])
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