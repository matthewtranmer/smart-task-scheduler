import socket
from multiprocessing import Process
import os
import sys, json, traceback
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from keras.preprocessing import image
import numpy as np
from PIL import Image
import io
import multiprocessing as mp
import base64
import os
import time

# ImageNet class indices for MobileNetV2
ORANGE_IDX = 950
BANANA_IDX = 954

def isFruitOrangeOrBanana(img_bytes: bytes, model):

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

    THRESH = 0.2

    if banana_conf >= orange_conf and banana_conf > THRESH:
        return "banana"
    if orange_conf > banana_conf and orange_conf > THRESH:
        return "orange"

    return "none"

def decode_image(image_in: str) -> bytes:
    return base64.decodebytes(image_in.encode())

def worker(sock, model):
    # This runs in the child process
    pid = os.getpid()
    print(f"pid {pid} started")

    while True:
        try:
            # Receive from parent
            length = int.from_bytes(sock.recv(4))
            # could not read all
            data = b""
            while len(data) != length:
                data += sock.recv(length)

            print(f"[child {pid}] received cmd")

            start = time.perf_counter()
            reply = isFruitOrangeOrBanana(data, model).encode()
            end = time.perf_counter()
            print(f"{pid}: {end-start}")

            sock.sendall(int.to_bytes(len(reply), length=4))
            sock.sendall(reply)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    # Load the pretrained model into memory
    model = MobileNetV2(
        weights='/Users/matthewtranmer/repos/smart-task-scheduler/docker/src/tasks/classify_fruit/mobilenet_v2_weights.h5',
        include_top=True
    )

    with open("/Users/matthewtranmer/repos/smart-task-scheduler/local/orange.jpg", "rb") as file:
        img_data = file.read()

    isFruitOrangeOrBanana(img_data, model)

    input("Boot start")

    sockets = []
    for i in range(2):
        # Create a connected pair of sockets
        parent_sock, child_sock = socket.socketpair()

        # Spawn child and give it one end
        p = Process(target=worker, args=(child_sock, model))
        p.start()

        # Parent no longer needs child's end
        sockets.append(parent_sock)

    input("send requests")

    for sock in sockets:
        for i in range(2):
            sock.sendall(int.to_bytes(len(img_data), length=4, signed=False))
            sock.sendall(img_data)

            # Receive reply
            length = int.from_bytes(sock.recv(4))
            response = sock.recv(length)
            print("[parent] got:", response)