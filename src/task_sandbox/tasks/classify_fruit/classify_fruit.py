# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TensorFlow INFO and WARNING logs

import numpy as np
from PIL import Image
import io
import multiprocessing as mp


# ImageNet class indices for MobileNetV2
ORANGE_IDX = 950
BANANA_IDX = 954

def isFruitOrangeOrBanana(img_bytes: bytes):
    # Large imports - load into memory when needed
    from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
    from keras.preprocessing import image

    # Load the pretrained model into memory
    model = MobileNetV2(
        weights='/app/tasks/classify_fruit/mobilenet_v2_weights.h5',
        include_top=True
    )
    
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((224, 224))

    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # Predict
    preds = model.predict(x, verbose=0)[0]  # shape (1000,)

    # Grab just banana + orange confidences
    banana_conf = float(preds[BANANA_IDX])
    orange_conf = float(preds[ORANGE_IDX])

    # (Optional) threshold so tiny activations don't count
    THRESH = 0.2

    if banana_conf >= orange_conf and banana_conf > THRESH:
        return "banana"
    if orange_conf > banana_conf and orange_conf > THRESH:
        return "orange"

    return None

def classifyFruit(img_bytes: bytes):
    with mp.Pool(1) as pool:
        response = pool.apply(isFruitOrangeOrBanana, args=(img_bytes,))

    return response