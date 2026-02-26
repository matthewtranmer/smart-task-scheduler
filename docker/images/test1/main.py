import os
os.environ["ORT_LOG_SEVERITY_LEVEL"] = "3"  # errors only

import numpy as np
import cv2
from PIL import Image
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

def remove_bg(image_bytes: bytes) -> Image:
    # Lazy load
    with suppress_stderr_fd():
        import onnxruntime as ort

    so = ort.SessionOptions()
    so.log_severity_level = 3  # errors only

    session = ort.InferenceSession("/app/u2netp.onnx")
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

    # --- Inference ---
    mask = session.run(None, {input_name: img})[0]

    # --- Postprocess ---
    mask = mask[0, 0]
    mask = (mask - mask.min()) / (mask.max() - mask.min() + 1e-8)
    mask = (mask * 255).astype(np.uint8)
    mask = cv2.resize(mask, (w, h))

    # --- Apply alpha ---
    rgba = cv2.cvtColor(orig, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask

    rgba_rgb = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA)

    return Image.fromarray(rgba_rgb)


# Returns the coordinates of a maximum of 5x5 adjacent pixels
def get_adjacent_pixels(x, y, width, height):
    pixels = []

    current_x = -2
    current_y = -2

    while current_y != 3:
        new_x = x + current_x
        new_y = y + current_y

        current_x += 1

        if current_x > 1:
            current_x = -1
            current_y += 1

        if (current_x == 0 and current_y == 0):
            continue

        if new_x < 0 or new_x >= width:
            continue

        if new_y < 0 or new_y >= height:
            continue

        pixels.append((new_x, new_y))

    return pixels


def calculate_fruit_defects(img_bytes: bytes):
    output_image: Image = remove_bg(img_bytes)
    output_image: Image = output_image.convert("RGBA").copy()
    output_image.save("out.png")

    pixels = output_image.load()
    width, height = output_image.size
    background_pixels = 0

    # Set background white
    for y in range(height):
        for x in range(width):
            R, G, B, A = pixels[x, y]
            if A < 100:
                pixels[x, y] = 255, 255, 255, 255
                background_pixels += 1

    image_copy = output_image.copy().load()
                
    # Remove black border
    for y in range(height):
        for x in range(width):
            R, G, B, A = image_copy[x, y]
            if R == 255 and G == 255 and B == 255:
                adjacent_pixels = get_adjacent_pixels(x, y, width, height)

                for adjacent_pixel in adjacent_pixels:
                    adjacent_x, adjacent_y = adjacent_pixel
                    if (image_copy[adjacent_x, adjacent_y] != (255, 255, 255, 255)):
                        pixels[adjacent_x, adjacent_y] = (255, 255, 255, 255)

    # Convert image to grayscale
    greyscale_img = output_image.convert("L")
    greyscale_pixels = greyscale_img.load()

    # Detect number of black pixels (pixels less than 130)
    black_pixels = 0

    for y in range(height):
        for x in range(width):
            if greyscale_pixels[x, y] < 85:
                black_pixels += 1


    foreground_pixels = width * height - background_pixels
    black_pixel_ratio = black_pixels/foreground_pixels

    print(f"foreground_pixels :{foreground_pixels}")
    print(f"black_pixels :{black_pixels}")

    return str(black_pixel_ratio).encode()


def fruit_defects(img_bytes: bytes):
    with mp.Pool(1) as pool:
        return pool.apply(calculate_fruit_defects, args=(img_bytes,))


with open("/app/ballon.png", "rb") as file:
    image_bytes = file.read()

print(fruit_defects(image_bytes))

while (True): pass