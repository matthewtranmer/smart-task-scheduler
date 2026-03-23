import io
import base64
import json
import multiprocessing as mp

import numpy as np
from PIL import Image

from lib.task_definitions import TaskIDs

def calculate_fruit_defects(json_data: bytes):
    data_dict = json.loads(json_data)

    img_data_b64_bytes = data_dict[str(TaskIDs.REMOVE_BACKGROUND)].encode()
    img_bytes = base64.decodebytes(img_data_b64_bytes)

    output_image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    arr = np.array(output_image, dtype=np.uint8)  # shape: (H, W, 4)

    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    # Step 1: set transparent-ish background to white
    background_mask = alpha < 100
    background_pixels = int(background_mask.sum())
    arr[background_mask] = [255, 255, 255, 255]

    # Step 2: remove black/dark border next to white background
    # A pixel is considered white if RGB == 255,255,255
    rgb = arr[:, :, :3]
    white_mask = np.all(rgb == 255, axis=2)

    # Find pixels within a 5x5 neighborhood of any white pixel.
    # This replaces the Python get_adjacent_pixels loop.
    near_white = np.zeros_like(white_mask, dtype=bool)

    h, w = white_mask.shape
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx == 0 and dy == 0:
                continue

            src_y0 = max(0, -dy)
            src_y1 = min(h, h - dy)
            src_x0 = max(0, -dx)
            src_x1 = min(w, w - dx)

            dst_y0 = max(0, dy)
            dst_y1 = min(h, h + dy)
            dst_x0 = max(0, dx)
            dst_x1 = min(w, w + dx)

            near_white[dst_y0:dst_y1, dst_x0:dst_x1] |= white_mask[src_y0:src_y1, src_x0:src_x1]

    # Remove non-white pixels that are adjacent to white background
    border_mask = near_white & (~white_mask)
    arr[border_mask] = [255, 255, 255, 255]

    # Step 3: grayscale and dark pixel count
    # PIL grayscale uses approximately 0.299 R + 0.587 G + 0.114 B
    rgb = arr[:, :, :3].astype(np.float32)
    greyscale = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]

    black_pixels = int((greyscale < 85).sum())

    foreground_pixels = (h * w) - background_pixels
    black_pixel_ratio = black_pixels / foreground_pixels if foreground_pixels > 0 else 0.0

    return str(black_pixel_ratio).encode()


def fruit_defects(json_data: bytes):
    with mp.Pool(1) as pool:
        return pool.apply(calculate_fruit_defects, args=(json_data,))