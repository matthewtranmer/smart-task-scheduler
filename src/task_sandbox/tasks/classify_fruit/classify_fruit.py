# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TensorFlow INFO and WARNING logs

from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from keras.preprocessing import image
import numpy as np
from PIL import Image
import io

def classifyFruit(img_bytes: bytes):
    # Load the pretrained model into memory
    model = MobileNetV2(weights='/app/tasks/classify_fruit/mobilenet_v2_weights.h5', include_top=True)
    
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((224, 224))

    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # Predict
    preds = model.predict(x, verbose=0)
    decoded = decode_predictions(preds, top=5)[0]

    # Check for apple, banana, or orange
    fruit_labels = ['banana', 'orange']
    for lbl, name, conf in decoded:
        if name in fruit_labels:
            return name, float(conf)
        
    return None, None