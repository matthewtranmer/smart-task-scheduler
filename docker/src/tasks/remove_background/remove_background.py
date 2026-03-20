import numpy as np
import cv2
from PIL import Image
import multiprocessing as mp
import time
import io
import json

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

def remove_bg(image_bytes: bytes) -> Image:
    # Lazy load
    t0 = time.perf_counter()
    import onnxruntime as ort
    t1 = time.perf_counter()

    import_time = t1 - t0

    t0 = time.perf_counter()
    session = ort.InferenceSession("/app/src/tasks/remove_background/.u2net/u2netp.onnx")
    t1 = time.perf_counter()

    model_load_time = t1 - t0

    t0 = time.perf_counter()
    input_name = session.get_inputs()[0].name

    # --- Decode image ---
    np_arr = np.frombuffer(image_bytes, np.uint8)
    orig = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if orig is None:
        raise ValueError("Invalid image bytes")

    h, w = orig.shape[:2]

    # --- Preprocess ---
    img = cv2.resize(orig, (320, 320))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))[None]

    t0 = time.perf_counter()
    # --- Inference ---
    mask = session.run(None, {input_name: img})[0]
    t1 = time.perf_counter()
    inference_time = t1 - t0

    # --- Postprocess ---
    mask = mask[0, 0]
    mask = (mask - mask.min()) / (mask.max() - mask.min() + 1e-8)
    mask = (mask * 255).astype(np.uint8)
    mask = cv2.resize(mask, (w, h))

    # --- Apply alpha ---
    rgba = cv2.cvtColor(orig, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask

    rgba_rgb = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA)

    times = {
        "import_time": import_time,
        "model_load_time": model_load_time,
        "inference_time": inference_time,
    }

    with open("timing.json", "w+") as file:
        file.write(json.dumps(times))

    return Image.fromarray(rgba_rgb)


def main(img_bytes: bytes) -> bytes:
    with suppress_stderr_fd():
        output_image: Image = remove_bg(img_bytes)
        
    buffer = io.BytesIO()
    output_image.save(buffer, format='PNG')

    return buffer.getvalue()



def remove_background(img_bytes: bytes) -> bytes:
    with mp.Pool(1) as pool:
        return pool.apply(main, args=(img_bytes,))