import socket, threading, logging
from lib import edge_pb2, net
from lib.scheduler import Scheduler

#ip, port, hasHeartbeat
edge_clients = []
heartbeat_timeout_s = 30
scheduler = Scheduler()
logger = logging.getLogger(__name__)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 2004))

server.listen()

# Find the index of the edge client by its address. Returns -1 on failure
def searchEdgeClients(addr):
    index = 0
    for client in edge_clients:
        if (client["IP"] == addr[0] and client["port"] == addr[1]):
            return index
        
        index += 1

    return -1

# Scan through all edge clients. If the client has timed out flag set to true then 
# remove it from the clients list. If the client hasn't timed out, set the flag so 
# that it has timed out. The heartbeat function will reset the flag so that it is 
# not removed on the next pass.
# Reinvoked asynchronously every heartbeat_timeout_s
def removeDeadClients():
    logger.debug(edge_clients)

    index = 0
    for client in edge_clients:
        if (client["has_timed_out"] == True):
            logger.info(f"Removed dead client {client} at index {index}")
            edge_clients.pop(index)
        else:
            client["has_timed_out"] = True

        index += 1
    logger.debug(edge_clients)

    threading.Timer(heartbeat_timeout_s, removeDeadClients).start()

# Called when a task is submitted to the access server by a client.
def scheduleTask(header, raw_payload):
    scheduled_index = scheduler.schedule(edge_clients)
    if (scheduled_index == -1):
        return net.createResponse(False, "There are no avaiable clients to perform the task").SerializeToString()

    scheduled_node = edge_clients[scheduled_index]

    logger.info(f"Scheduled task on node {scheduled_node}")

    edge_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    edge_connection.connect((scheduled_node["IP"], scheduled_node["port"]))

    net.send(edge_connection, header, raw_payload)
    _, response = net.recv(edge_connection)

    return response


# Called when an edge client sends a heartbeat signal. Sets the client's 
# has timed out flag to false. 
def heartbeat(raw_payload):
    heartbeat_payload = edge_pb2.Heartbeat()
    heartbeat_payload.ParseFromString(raw_payload)

    ip = socket.inet_ntop(socket.AF_INET, heartbeat_payload.IP)
    port = heartbeat_payload.port

    logger.info(f"Received heartbeat from {ip}:{port}")

    index = searchEdgeClients((ip, port))
    if index != -1:
        edge_clients[index]["has_timed_out"] = False
        
        return net.createResponse(True, b"Success").SerializeToString()
    
    return net.createResponse(False, b"Edge node does not exist!").SerializeToString()

# Registers an edge client as alive. Adds its IP, port and its timed out flag
# to the list of edge clients.
def edgeNodeRegistration(raw_payload):
    registration = edge_pb2.Registration()
    registration.ParseFromString(raw_payload)

    ip = socket.inet_ntop(socket.AF_INET, registration.IP)
    port = registration.port

    # Ensure client isn't already registered
    index = searchEdgeClients((ip, port))
    if index != -1:
        return net.createResponse(False, b"Client already exists in the registry!")

    # Add client to the registry
    edge_clients.append({
        "IP": ip,
        "port": port,
        "has_timed_out": False
    })

    logger.info(f"Regstering node {ip}:{port}")

    return net.createResponse(True, b"Success").SerializeToString()

def handleRequest(sock, addr):
    parsed_header, raw_payload = net.recv(sock)
    response = b""

    match parsed_header.commandID:
        # Schedule task
        case net.Commands.SCHEDULE_TASK:
            response = scheduleTask(parsed_header, raw_payload)
        # Heartbeat
        case net.Commands.HEARTBEAT:
            response = heartbeat(raw_payload)
        # Edge node registration
        case net.Commands.REGISTRATION:
            response = edgeNodeRegistration(raw_payload)

    header = net.createHeader(parsed_header.commandID)
    net.send(sock, header, response)

def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    removeDeadClients()

    while True:
        sock, addr = server.accept()

        handleRequest(sock, addr)

if __name__ == "__main__":
    main()


# Edge access functions:
# Take in task and schedule it on an edge node
# Take in an edge node and add it to list of schedulable nodes
# Take in heartbeat signal from each node

# Request:
# Command ID
# Parameters