import io
import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite
import multiprocessing as mp
import os, sys
from contextlib import contextmanager

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

# Uses the trained model to predict the quality of a banana
# Returns True when predicted fresh, False when bad
def isFruitFresh(image_bytes: bytes, interpreter, input_details, output_details) -> bool:
    # Load and preprocess image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((150, 150))

    x = np.array(img, dtype=np.float32)
    x = x / 255.0  # same normalization as before
    x = np.expand_dims(x, axis=0)  # [1, 150, 150, 3]

    # Feed input to the interpreter
    interpreter.set_tensor(input_details[0]["index"], x)

    # Run inference
    interpreter.invoke()

    # Get prediction
    output_data = interpreter.get_tensor(output_details[0]["index"])
    prediction = float(output_data[0][0])  # scalar between 0 and 1

    return prediction >= 0.5

def main(image_bytes: bytes):
    TFLITE_MODEL_PATH = "/app/src/tasks/fruit_quality/banana_freshness.tflite"

    with suppress_stderr_fd():
        # Create and allocate the interpreter once, at import time
        interpreter = tflite.Interpreter(model_path=TFLITE_MODEL_PATH)
        # interpreter = TFLiteInterpreter(model_path=TFLITE_MODEL_PATH)  # if using TF instead
        interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    return isFruitFresh(image_bytes, interpreter, input_details, output_details)

def fruitQuality(image_bytes: bytes):
    with mp.Pool(1) as pool:
        response = pool.apply(main, args=(image_bytes,))

    return response
