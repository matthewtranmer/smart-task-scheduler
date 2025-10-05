import socket
import edge_pb2

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 2004))

server.listen()

def recv(sock):
    header_length_bytes = sock.recv(4)
    header_length = int.from_bytes(header_length_bytes, byteorder="little", signed=False)

    header_bytes = sock.recv(header_length)

    parsed_header = edge_pb2.Header()
    parsed_header.ParseFromString(header_bytes)

    raw_payload = sock.recv(parsed_header.messageLength)

    return (parsed_header, raw_payload)

def scheduleTask():
    pass

def heartbeat():
    pass

def edgeNodeDiscovery():
    pass

def handleRequest(sock, addr):
    parsed_header, raw_payload = recv(sock)
    
    match parsed_header.commandID:
        # Schedule task
        case 1:
            pass
        # Heartbeat
        case 2:
            pass
        # Edge node discovery
        case 3:
            pass

while True:
    sock, addr = server.accept()

    handleRequest(sock, addr)




# Edge access functions:
# Take in task and schedule it on an edge node
# Take in an edge node and add it to list of schedulable nodes
# Take in heartbeat signal from each node

# Request:
# Command ID
# Parameters