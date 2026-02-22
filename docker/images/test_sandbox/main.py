import sys, json, traceback
from src import task
from lib import edge_pb2

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

    with open("src/user/test_data/human.jpg", "rb") as f:
        image_bytes = f.read()

    input_id = 2
    result = task.run_task(input_id, image_bytes)

    print(result)

    # response = edge_pb2.ContainerResponse()
    # response.inputID = input_id
    # response.value = result
    # response.error = False
    # serialized_response = response.SerializeToString()



if __name__ == "__main__":
    main()