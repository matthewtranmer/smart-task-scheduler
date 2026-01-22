from PIL import Image
import numpy as np
from scipy import ndimage

img = Image.open("/Users/matthewtranmer/repos/smart-task-scheduler/local/object_count/out.png").convert("L")

arr = np.array(img)

binary = arr < 240
labels, count = ndimage.label(binary)

print("Objects:", count)
