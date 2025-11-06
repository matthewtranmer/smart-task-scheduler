# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU
# os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TensorFlow INFO and WARNING logs

import numpy as np
import multiprocessing as mp
import io
from PIL import Image


# Uses the trained model to predict the quality of a banana
# Returns True when predicted fresh, False when bad
def isFruitFresh(image_bytes: bytes):
    # Large imports - load into memory when needed
    from keras.models import load_model
    from keras.preprocessing import image

    # Load trained model into memory
    model = load_model("/app/tasks/fruit_quality/banana_freshness_model_final.h5", compile=False)  # or banana_freshness_model_final.h5

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((150, 150))

    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0)  # batch dimension

    prediction = model.predict(x, verbose=0)[0][0]  # scalar between 0 and 1

    if prediction >= 0.5:
        return True
    
    return False

def fruitQuality(image_bytes: bytes):
    with mp.Pool(1) as pool:
        response = pool.apply(isFruitFresh, args=(image_bytes,))

    return response
