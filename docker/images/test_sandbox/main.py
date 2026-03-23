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

    FRUIT_SIZE = 9
    FRUIT_DEFECTS = 10
    REMOVE_BACKGROUND = 13

    print("Starting background removal")
    t0 = time.perf_counter()

    no_background = json.dumps({
        "13": base64.encodebytes(task.run_task(REMOVE_BACKGROUND, image_bytes)).decode()
    })

    t1 = time.perf_counter()
    print(f"Background removal finished. Execution: {t1 - t0}")

    print("Starting defects")
    t0 = time.perf_counter()

    defects = task.run_task(FRUIT_DEFECTS, no_background)
    print(f"defects: {defects}")

    t1 = time.perf_counter()
    print(f"Finishing defects. Execution: {t1 - t0}")

    # print("Waiting 5 seconds....")
    # time.sleep(5)

    # print("Running....")

    # result = task.run_task(current_task, image_bytes)
    # print(result)

    # input("Press enter to continue...")

    time.sleep(1000000)




    # with open("src/user/test_data/human.jpg", "rb") as f:
    #     image_bytes = f.read()

    # input_id = 2
    # result = task.run_task(input_id, image_bytes)

    # print(result)

    # response = edge_pb2.ContainerResponse()
    # response.inputID = input_id
    # response.value = result
    # response.error = False
    # serialized_response = response.SerializeToString()



if __name__ == "__main__":
    main()