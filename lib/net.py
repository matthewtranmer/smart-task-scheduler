from lib import edge_pb2
from enum import Enum

class Commands(Enum):
    SCHEDULE_TASK = 1
    HEARTBEAT = 2
    REGISTRATION = 3

def createHeader(commandID):
    header = edge_pb2.Header()
    header.commandID = commandID

    return header

def send(sock, header, data):
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

    raw_payload = sock.recv(parsed_header.messageLength)

    return (parsed_header, raw_payload)