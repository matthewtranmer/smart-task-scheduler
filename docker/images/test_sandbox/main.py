print("First line")

# while (True): pass

import sys, json, traceback, time
from src import task
from lib import edge_pb2
import base64

print("Finished imports")

# def read_data() -> bytes:
#     length_bytes = sys.stdin.buffer.read(4)
#     buffer_length = int.from_bytes(length_bytes, byteorder="big", signed=False)

#     received_data = b""
#     while len(received_data) < buffer_length:
#         received_data += sys.stdin.buffer.read(buffer_length - len(received_data))

#     return received_data

# def write_data(data: bytes):
#     sys.stdout.buffer.write(len(data).to_bytes(4, byteorder="big", signed=False) + data)
#     sys.stdout.buffer.flush()

def main():
    print("Started!")
    with open("/app/orange.png", "rb") as f:
        image_bytes = f.read()

    REMOVE_BACKGROUND = 13

    print("Starting background removal")

    t0 = time.perf_counter()
    task.run_task(REMOVE_BACKGROUND, image_bytes)
    t1 = time.perf_counter()

    print(f"Background removal finished. Execution: {t1 - t0}")

    time.sleep(1000000)


if __name__ == "__main__":
    main()