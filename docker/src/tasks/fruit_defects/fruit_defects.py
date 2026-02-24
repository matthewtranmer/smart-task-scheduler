from rembg import remove, new_session
from PIL import Image
import io

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


def fruit_defects(img_bytes: bytes):
    input_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    session = new_session("u2netp")
    output_image = remove(input_image, session)

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

    return str(black_pixel_ratio).encode()