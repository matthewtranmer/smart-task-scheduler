import io, json
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

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    e = np.exp(x)
    return e / np.sum(e)

def preprocess(img_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((224, 224))
    x = np.asarray(img, dtype=np.float32) / 255.0       # HWC, 0..1
    x = (x - IMAGENET_MEAN) / IMAGENET_STD              # normalize
    x = np.expand_dims(x, axis=0).astype(np.float32)    # NHWC
    return x

def getBananaRipeness_tflite(img_bytes: bytes, model_path: str, idx_to_class: dict) -> str:
    with suppress_stderr_fd():
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()

    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]

    x = preprocess(img_bytes)

    # Most float models want float32 input; if yours wants float16, cast.
    if inp["dtype"] == np.float16:
        x = x.astype(np.float16)

    interpreter.set_tensor(inp["index"], x)
    interpreter.invoke()

    logits = interpreter.get_tensor(out["index"])[0].astype(np.float32)
    probs = softmax(logits)
    pred_idx = int(np.argmax(probs))
    return idx_to_class[pred_idx].encode()

def main(img_bytes: bytes) -> str:
    class_to_idx = {"fresh": 0, "rotten": 1, "unripe": 2}
    idx_to_class = {int(v): k for k, v in class_to_idx.items()}  # ensure int keys

    return getBananaRipeness_tflite(
        img_bytes,
        model_path="/app/src/tasks/banana_quality/ripeness/banana_ripeness_resnet18_float32.tflite",
        idx_to_class=idx_to_class
    )

def ripeness(img_bytes: bytes) -> str:
    with mp.Pool(1) as pool:
        return pool.apply(main, args=(img_bytes,))