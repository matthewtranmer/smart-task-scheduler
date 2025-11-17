from lib import edge_pb2
import socket

class Commands():
    SCHEDULE_TASK = 1
    HEARTBEAT = 2
    REGISTRATION = 3
    GATHER_DIAGNOSTICS = 4

def createHeader(commandID):
    header = edge_pb2.Header()
    header.commandID = commandID

    return header

def createResponse(success: bool, value: bytes) -> edge_pb2.Response:
    response = edge_pb2.Response()
    response.success = success
    response.value = value

    return response

def createTask(taskID: int, input: bytes, memory_requirement_mb: int, deadline_ms: int, inputID: int):
    task = edge_pb2.Task()
    task.taskID = taskID
    task.input = input
    task.memory_requirement_mb = memory_requirement_mb
    task.deadline_ms = deadline_ms
    task.inputID = inputID

    return task

def send(sock, header: edge_pb2.Header, data: bytes):
    header.messageLength = len(data)

    header_bytes = header.SerializeToString()
    header_length = len(header_bytes).to_bytes(4, byteorder="little", signed=False)
    
    sock.sendall(header_length + header_bytes + data)

def recv(sock): 
    header_length_bytes = sock.recv(4)
    header_length = int.from_bytes(header_length_bytes, byteorder="little", signed=False)

    header_bytes = sock.recv(header_length)

    parsed_header = edge_pb2.Header()
    parsed_header.ParseFromString(header_bytes)

    raw_payload = b""
    bytes_read = 0
    while bytes_read < parsed_header.messageLength:
        buffer = sock.recv(parsed_header.messageLength)
        bytes_read += len(buffer)
        raw_payload += buffer

    return (parsed_header, raw_payload)

# Get IP of local machine
def getLocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to google DNS IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

