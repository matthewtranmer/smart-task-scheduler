print("FRUIT SIZE 1")
from rembg import remove, new_session
print("FRUIT SIZE 2")

from PIL import Image
import io

def fruit_size(img_bytes: bytes):
    input_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    session = new_session("u2netp")
    output_image = remove(input_image, session=session)
    
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