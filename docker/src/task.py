import base64
from lib.scheduler import Tasks

from src.tasks.detect_human.detect_human import detectHuman
from src.tasks.classify_fruit.classify_fruit import classifyFruit
from src.tasks.fruit_quality.fruit_quality import fruitQuality
from src.tasks.compression.compression import compress, decompress
from src.tasks.encryption.encryption import encrypt, decrypt

from src.tasks.banana_ripeness.ripeness import ripeness as banana_ripeness
from src.tasks.orange_ripeness.ripeness import ripeness as orange_ripeness

from src.tasks.fruit_defects.fruit_defects import fruit_defects 
from src.tasks.fruit_size.fruit_size import fruit_size

from src.tasks.object_count.object_count import object_count

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
        
        case Tasks.BANANA_QUALITY_RIPENESS:
            result = banana_ripeness(data)
        case Tasks.ORANGE_QUALITY_RIPENESS:
            result = orange_ripeness(data)

        case Tasks.FRUIT_DEFECTS:
            result = fruit_defects(data)
        case Tasks.FRUIT_SIZE:
            result = fruit_size(data)
        
        case Tasks.OBJECT_COUNT:
            result = object_count(data)

        # Test tasks
        case Tasks.ADDITION:
            result = addition(data)
        case Tasks.MULTIPLICATION:
            result = multiplication(data)
        case Tasks.DIVISION:
            result = division(data)

    return result