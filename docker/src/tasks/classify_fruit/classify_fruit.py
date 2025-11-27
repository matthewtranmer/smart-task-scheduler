import tflite_runtime.interpreter as tflite
import io
from PIL import Image
import numpy as np
import multiprocessing as mp
import os, sys
from contextlib import contextmanager

ORANGE_IDX = 950
BANANA_IDX = 954

@contextmanager
def suppress_stderr_fd():
    """
    Temporarily redirect the OS-level stderr (fd 2) to /dev/null.
    This catches C/C++ library prints like TFLite's XNNPACK info.
    """
    stderr_fd = sys.stderr.fileno()

    # Save a copy of the current stderr fd
    saved_stderr_fd = os.dup(stderr_fd)

    try:
        # Open /dev/null and dup it over stderr
        with open(os.devnull, 'w') as devnull:
            os.dup2(devnull.fileno(), stderr_fd)
        yield
    finally:
        # Restore original stderr
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(saved_stderr_fd)

def isFruitOrangeOrBanana(img_bytes: bytes, interpreter, input_index: int, output_index: int):
    # Decode + resize
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((224, 224))

    # Convert to array (float32), shape (1, 224, 224, 3)
    x = np.array(img, dtype=np.float32)
    x = np.expand_dims(x, axis=0)

    # MobileNetV2 preprocess_input (tf mode): scale to [-1, 1]
    x = (x / 127.5) - 1.0

    # Set input tensor
    interpreter.set_tensor(input_index, x)

    # Run inference
    interpreter.invoke()

    # Get output tensor (shape: (1, 1000))
    preds = interpreter.get_tensor(output_index)[0]

    # Grab just banana + orange confidences
    banana_conf = float(preds[BANANA_IDX])
    orange_conf = float(preds[ORANGE_IDX])

    THRESH = 0.2

    if banana_conf >= orange_conf and banana_conf > THRESH:
        return "banana"
    if orange_conf > banana_conf and orange_conf > THRESH:
        return "orange"

    return "none"

def main(img_bytes: bytes) -> bytes:
    # Load model
    with suppress_stderr_fd():
        interpreter = tflite.Interpreter(model_path="/app/src/tasks/classify_fruit/mobilenet_v2_imagenet.tflite")
        interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_index = input_details[0]["index"]
    output_index = output_details[0]["index"]

    return isFruitOrangeOrBanana(img_bytes, interpreter, input_index, output_index).encode()

def classifyFruit(img_bytes: bytes) -> bytes:
    with mp.Pool(1) as pool:
        response = pool.apply(main, args=(img_bytes,))

    return response