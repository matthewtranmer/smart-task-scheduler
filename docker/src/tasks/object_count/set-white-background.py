from PIL import Image
import numpy as np
from scipy import ndimage

img = Image.open("/Users/matthewtranmer/repos/smart-task-scheduler/local/object_count/orange2.png").convert("RGBA")

pixels = img.load()
width, height = img.size

for y in range(height):
    for x in range(width):
        R, G, B, A = pixels[x, y]
        if A < 100:
            pixels[x, y] = 255, 255, 255, 255
            print(1)


# img = img.convert("L")
img.save("/Users/matthewtranmer/repos/smart-task-scheduler/local/object_count/test.png")
arr = np.array(img)

binary = arr < 240
labels, count = ndimage.label(binary)

print("Objects:", count)
