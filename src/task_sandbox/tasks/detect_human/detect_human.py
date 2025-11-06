# import os

# # Move CWD to a writable place *before* importing anything that uses Ultralytics
# os.chdir("/mnt/data")

import cv2, os
import numpy as np
from contextlib import redirect_stdout, redirect_stderr
import multiprocessing as mp

def imageContainsHuman(image: np.ndarray) -> bool:
    # Large imports - load into memory when needed
    # Silence Ultralytics' import-time output
    with open(os.devnull, "w") as f, redirect_stdout(f), redirect_stderr(f):
        from ultralytics import YOLO

    # Load YOLO model into memory
    model = YOLO("/app/tasks/detect_human/yolov8n.pt") 
    conf_threshold = 0.35

    # Run inference
    results = model.predict(image, conf=conf_threshold, verbose=False)

    # YOLO uses COCO class IDs; 0 = 'person'
    PERSON_CLASS_ID = 0
    
    contains_human = False

    for r in results:
        if r.boxes is None:
            continue

        for cls_id, score in zip(r.boxes.cls, r.boxes.conf):
            if int(cls_id.item()) == PERSON_CLASS_ID and float(score.item()) >= conf_threshold:
                contains_human = True
                break
    
    return contains_human

def parseImageBytes(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image from bytes")

    return img

def detectHuman(image_bytes) -> bool:
    image = parseImageBytes(image_bytes)

    with mp.Pool(1) as pool:
        response = pool.apply(imageContainsHuman, args=(image,))

    return response

