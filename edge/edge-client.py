import socket, time
from lib import edge_pb2, net

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))

ip, port = server.getsockname()

server.listen()

# Send an still alive signal to the access server. 
def sendHeartbeat():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 2004))

    header = net.createHeader(net.Commands.HEARTBEAT)

    heartbeat = edge_pb2.Heartbeat()
    heartbeat.IP = socket.inet_pton(socket.AF_INET, ip)
    heartbeat.port = port
    heartbeat_bytes = heartbeat.SerializeToString()

    net.send(client, header, heartbeat_bytes)

# Register the node as alive with the access server
def registerNode():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 2004))
    
    header = net.createHeader(net.Commands.REGISTRATION)

    registration = edge_pb2.Registration()
    registration.IP = socket.inet_pton(socket.AF_INET, ip)
    registration.port = port
    registration_bytes = registration.SerializeToString()

    net.send(client, header, registration_bytes)
    print("sent")

def handleRequest(sock, addr):
    parsed_header, raw_payload = net.recv(sock)    

# while True:
#     sock, addr = server.accept()

#     handleRequest(sock, addr)

registerNode()
while True:
    sendHeartbeat()
    print("sent heartbeat!")

    time.sleep(5)