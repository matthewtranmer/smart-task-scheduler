import socket
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from keras.preprocessing import image
import numpy as np
from PIL import Image
import io
import base64
import os
import time
import resource, psutil



import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # avoid CUDA errors, force CPU
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TensorFlow INFO and WARNING logs

with open("/home/matthew/repos/smart-task-scheduler/local/tests/tasks/classify-fruit/banana/1.jpg", "rb") as file:
    img_data = file.read()


def get_memory_usage_all():
    parent = psutil.Process(os.getpid())
    procs = [parent] + parent.children(recursive=True)

    results = []
    total_rss = 0

    for p in procs:
        try:
            mem = p.memory_info()
            rss = mem.rss
            shared = getattr(mem, "shared", 0)  # not available on all platforms
            private = rss - shared
            results.append({
                "pid": p.pid,
                "rss": rss,
                "shared": shared,
                "private": private
            })
            total_rss += rss
        except psutil.NoSuchProcess:
            pass

    return results, total_rss

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

def worker(sock):
    model = MobileNetV2(
        weights='/home/matthew/repos/smart-task-scheduler/docker/src/tasks/classify_fruit/mobilenet_v2_weights.h5',
        include_top=True
    )

    isFruitOrangeOrBanana(img_data, model)

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
    
    

    # isFruitOrangeOrBanana(img_data)

    input("Boot start")

    children = 16
    sockets = []
    for i in range(children):
        # Create a connected pair of sockets
        parent_sock, child_sock = socket.socketpair()

        pid = os.fork()
        print(pid)

        if pid == 0:
            print("child")
            worker(child_sock)
            os._exit(0)  # Child process exits after worker returns
        else:
            print("parent")

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

    results, total_rss = get_memory_usage_all()

    for r in results:
        print(
            f"PID {r['pid']}   "
            f"RSS={r['rss']/1024/1024:.2f} MB   "
            f"Shared={r['shared']/1024/1024:.2f} MB   "
            f"Private={r['private']/1024/1024:.2f} MB"
        )

    print(f"\nTOTAL RSS: {total_rss/1024/1024:.2f} MB")