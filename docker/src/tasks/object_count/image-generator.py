from PIL import Image
import numpy as np
from scipy import ndimage
import random

background_width = 3000
background_height = 3000
background = Image.new("RGB", (background_width, background_height), (255, 255, 255))

orange_width = 500
orange_height = 500
orange = Image.open("/Users/matthewtranmer/repos/smart-task-scheduler/local/object_count/orange-wb.png").resize((orange_width, orange_height))

def is_image_in_range(coords, coordinates_placed, dimensions):
    image_width = dimensions[0]
    image_height = dimensions[1]

    new_x1 = coords[0]
    new_x2 = coords[0] + image_width
    new_y1 = coords[1]
    new_y2 = coords[1] + image_height

    for px, py in coordinates_placed:
        existing_x1 = px
        existing_x2 = px + image_width
        existing_y1 = py
        existing_y2 = py + image_height

        not_overlapping = (
            new_x2 <= existing_x1 or 
            new_x1 >= existing_x2 or
            new_y2 <= existing_y1 or
            new_y1 >= existing_y2
        )

        is_overlapping = not not_overlapping
        if (is_overlapping):
            return True

    return False

coordinates_placed = []
while len(coordinates_placed) < 15:
    x = random.randint(0, background_width-1-orange_width)
    y = random.randint(0, background_height-1-orange_height)
    rand_coord = (x, y)

    if is_image_in_range(rand_coord, coordinates_placed, (orange_width, orange_height)):
        continue

    background.paste(orange, rand_coord)
    coordinates_placed.append(rand_coord)


background.save("/Users/matthewtranmer/repos/smart-task-scheduler/local/object_count/out.png")
