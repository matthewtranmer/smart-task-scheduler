import sys, json, traceback
from src import task
from lib import edge_pb2
import socket

# def read_data() -> bytes:
#     length_bytes = sys.stdin.buffer.read(4)
#     buffer_length = int.from_bytes(length_bytes, byteorder="big", signed=False)

#     received_data = b""
#     while len(received_data) < buffer_length:
#         received_data += sys.stdin.buffer.read(buffer_length - len(received_data))

#     return received_data

# def write_data(data: bytes):
#     payload_length = len(data)
#     payload_length_bytes = payload_length.to_bytes(4, byteorder="big", signed=False)

#     with open("/app/test_output.txt", "a") as file:
#         file.write(f"payload length: {payload_length}, payload_length_bytes:{payload_length_bytes}\n")

#     sys.stdout.buffer.write(payload_length_bytes)
#     sys.stdout.buffer.write(data)
#     sys.stdout.buffer.flush()

BUF_SIZE = 65536

def receive(sock: socket.socket):        
    payload = sock.recv(BUF_SIZE)
    if len(payload) < 4:
        raise ValueError("Header could not be read")
    
    length_bytes = payload[:4]        
    received_data = payload[4:]

    print(f"Length bytes: {length_bytes}")

    buffer_length = int.from_bytes(length_bytes, byteorder="big", signed=False)

    print(f"Buf length: {buffer_length}")

    while len(received_data) < buffer_length:
        payload = sock.recv(BUF_SIZE)
        received_data += payload

    print(f"Length of received data: {len(received_data)}")
    
    return received_data

def send(sock: socket.socket, data: bytes):
    length_header = len(data).to_bytes(4, "big", signed=False)

    sock.sendall(length_header + data)

def main():
    print("Starting init process...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 8000))
    sock.listen()

    print("1")

    conn, _ = sock.accept()

    print("Container started!")

    while True:
        try:
            input_data = receive(conn)
            print("Accepted request")

            incoming_task = edge_pb2.Task()
            incoming_task.ParseFromString(input_data)

            result = task.run_task(incoming_task.taskID, incoming_task.input) 
                
            response = edge_pb2.ContainerResponse()
            response.inputID = incoming_task.inputID
            response.value = result
            response.error = False
            serialized_response = response.SerializeToString()

            send(conn, serialized_response)

        except Exception as e:
            print("ERROR!")
            exception = traceback.format_exc()

            print(exception)

            response = edge_pb2.ContainerResponse()
            response.inputID = incoming_task.inputID
            response.traceback = exception.encode()
            response.error = True
            serialized_response = response.SerializeToString()
            
            send(conn, serialized_response)

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