import numpy as np
import io
from PIL import Image
import multiprocessing as mp

def calculate_fruit_size(img_bytes: bytes):
    output_image = Image.open(io.BytesIO(img_bytes))
    output_image: Image = output_image.convert("RGBA")
    
    img_pixels = output_image.getdata()

    background_pixels = 0
    for i in img_pixels:
        alpha = i[3]
        if alpha == 0:
            background_pixels += 1

    total_pixels = output_image.size[0] * output_image.size[1]
    foreground_pixels = total_pixels - background_pixels

    # Higer the ratio, the higher the foreground covers the screen
    foreground_background_ratio = foreground_pixels / background_pixels
    return str(foreground_background_ratio).encode()

def fruit_size(img_bytes: bytes):
    with mp.Pool(1) as pool:
        return pool.apply(calculate_fruit_size, args=(img_bytes,))