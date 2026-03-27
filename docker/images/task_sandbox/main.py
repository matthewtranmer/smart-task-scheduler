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
    while True:
        try:
            input_data = read_data()

            incoming_task = edge_pb2.Task()
            incoming_task.ParseFromString(input_data)

            result = task.run_task(incoming_task.taskID, incoming_task.input) 
            
            response = edge_pb2.ContainerResponse()
            response.inputID = incoming_task.inputID
            response.value = result
            response.error = False
            serialized_response = response.SerializeToString()

            with open("/app/test_output.txt", "a") as file:
                file.write(f"taskID: {incoming_task.taskID} - payload length: {len(serialized_response)}")

            write_data(serialized_response)

        except Exception as e:
            exception = traceback.format_exc()

            response = edge_pb2.ContainerResponse()
            response.inputID = incoming_task.inputID
            response.traceback = exception.encode()
            response.error = True
            serialized_response = response.SerializeToString()
            
            write_data(serialized_response)

if __name__ == "__main__":
    main()