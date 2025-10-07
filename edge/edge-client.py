import socket, time, threading, random
from lib import edge_pb2, net

heartbeat_interval = 30

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))

ip, port = server.getsockname()
server.listen()

print(f"Edge client started on address {ip}:{port}")

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
    _, response_bytes = net.recv(client)
    
    response = edge_pb2.Response()
    response.ParseFromString(response_bytes)

    print(response)

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
    _, response_bytes = net.recv(client)
    
    response = edge_pb2.Response()
    response.ParseFromString(response_bytes)

    print(response)

# Run the task on the current node
def runTask(task: edge_pb2.Task):
    print(f"Running task with id {task.taskID} and input {task.input} on node {ip}:{port}")

    sleep_time = random.uniform(0, 1)
    time.sleep(sleep_time)

    response = str(sleep_time).encode()
    print(f"Response generated as: {response}")

    return response

def handleRequest(sock, addr):
    parsed_header, raw_payload = net.recv(sock)   
    response_value = b"" 

    if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        response_value = runTask(task)

    if (response_value != ""):
        response = net.createResponse(True, response_value)
    else:
        response = net.createResponse(False, b"Error running task")

    header = net.createHeader(parsed_header.commandID)
    net.send(sock, header, response.SerializeToString())

# Function that sends a heartbeat to the access server every heartbeat_interval
# seconds.
def heartbeatSender():
    sendHeartbeat()
    print("sent heartbeat!")

    threading.Timer(heartbeat_interval, heartbeatSender).start()

def main():
    registerNode()
    heartbeatSender()

    while True:
        sock, addr = server.accept()
        sock.settimeout(2)

        handleRequest(sock, addr)

if __name__ == "__main__":
    main()