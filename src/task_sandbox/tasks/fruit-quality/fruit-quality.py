import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TensorFlow INFO and WARNING logs

import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Load trained model
model = load_model("local/tests/tasks/bad-fruit/banana_freshness_model_final.h5", compile=False)  # or banana_freshness_model_final.h5

# Uses the trained model to predict the quality of a banana
# Returns True when predicted fresh, False when bad
def predictBananaQuality(image_path):
    IMG_SIZE = (150, 150)

    img = image.load_img(image_path, target_size=IMG_SIZE)
    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0)  # batch dimension

    prediction = model.predict(x, verbose=0)[0][0]  # scalar between 0 and 1
    # Since we trained with binary class_mode='binary':
    # Usually 0 ~ class index 0, 1 ~ class index 1
    # Let's use threshold 0.5

    if prediction >= 0.5:
        return True
    
    return False

# Example use
if __name__ == "__main__":
    img_path = "local/tests/tasks/bad-fruit/brown.jpg"
    val = predictBananaQuality(img_path)
    print(val)
