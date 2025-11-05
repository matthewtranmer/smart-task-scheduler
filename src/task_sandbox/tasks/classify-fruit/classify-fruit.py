import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU

from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np

# Load the pretrained model
model = MobileNetV2(weights='imagenet')

def detectFruit(img_path):
    # Load and preprocess the image
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # Predict
    preds = model.predict(x)
    decoded = decode_predictions(preds, top=5)[0]

    # Check for apple, banana, or orange
    fruit_labels = ['banana', 'orange']
    for lbl, name, conf in decoded:
        if lbl in fruit_labels:
            return lbl, conf

    return None, None

result = detectFruit("local/tests/tasks/classify-fruit/orange/orange.jpg")
# result = detect_fruit("local/tests/tasks/classify-fruit/banana/1.jpg")
print("Detected:", result)
