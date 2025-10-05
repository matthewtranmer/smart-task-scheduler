import socket
import edge_pb2

task = edge_pb2.Task()
task.taskID = 0
task.input = b"Hello"

data = task.SerializeToString()

def send(sock, data):
    header = edge_pb2.Header()
    header.messageLength = len(data)
    header.commandID = 1

    header_bytes = header.SerializeToString()
    header_length = len(header_bytes).to_bytes(4, byteorder="little", signed=False)
    
    sock.sendall(header_length + header_bytes + data)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 2004))

send(sock, data)
print("Done")

sock.close()

