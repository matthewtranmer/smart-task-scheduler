print("First line")

# while (True): pass

import sys, json, traceback, time
from src import task
from lib import edge_pb2


print("Finished imports")

def read_data() -> bytes:
    length_bytes = sys.stdin.buffer.read(4)
    buffer_length = int.from_bytes(length_bytes, byteorder="big", signed=False)

    received_data = b""
    while len(received_data) < buffer_length:
        received_data += sys.stdin.buffer.read(buffer_length - len(received_data))

    return received_data

def write_data(data: bytes):
    sys.stdout.buffer.write(len(data).to_bytes(4, byteorder="big", signed=False) + data)
    sys.stdout.buffer.flush()

def main():
    print("Started!")
    with open("/app/orange.png", "rb") as f:
        image_bytes = f.read()

    FRUIT_SIZE = 9
    FRUIT_DEFECTS = 10

    current_task = 11

    print("Running....")

    result = task.run_task(current_task, image_bytes)
    print(result)

    print("Waiting....")
    time.sleep(5)

    print("Running....")

    result = task.run_task(current_task, image_bytes)
    print(result)

    while (True):
        pass




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