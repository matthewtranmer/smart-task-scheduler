from rembg import remove
from PIL import Image

input_image = Image.open("/home/matthew/repos/smart-task-scheduler/docker/src/tasks/banana_quality/size/okay.jpg")

output_image = remove(input_image)
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

print(f"Total pixels: {total_pixels}")
print(f"Foreground pixels: {foreground_pixels}")
print(f"Background pixels: {background_pixels}")
print(f"FB ratio: {foreground_background_ratio}")

output_image.save("/home/matthew/repos/smart-task-scheduler/docker/src/tasks/banana_quality/size/output.png")  # PNG keeps transparency
