from PIL import Image
import numpy as np
from scipy import ndimage
import io

def object_count(img_bytes: bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    arr = np.array(img)

    binary = arr < 240
    _, count = ndimage.label(binary)

    return str(count).encode()