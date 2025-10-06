import socket, threading
from lib import edge_pb2, net

#ip, port, hasHeartbeat
edge_clients = []
heartbeat_timeout_s = 5

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
    print(edge_clients)

    index = 0
    for client in edge_clients:
        if (client["has_timed_out"] == True):
            edge_clients.pop(index)
        else:
            client["has_timed_out"] = True

        index += 1
    print(edge_clients)

    threading.Timer(heartbeat_timeout_s, removeDeadClients).start()

# Returns the index of the next node to be scheduled in the edge clients list.
current_node = 0
def scheduler():
    if current_node >= len(edge_clients):
        current_node = 0

    # TODO: case when there are no nodes
    
    node_index = current_node
    current_node += 1

    return node_index

# Called when a task is submitted to the access server by a client.
# TODO: make thread safe
def scheduleTask():
    scheduled_index = scheduler()

    print(f"Index of node scheduled: {scheduled_index}")
    print(f"Node scheduled: {edge_clients[scheduled_index]}")

# Called when an edge client sends a heartbeat signal. Sets the client's 
# has timed out flag to false. 
# TODO: return error response if the client isn't in the list so that the 
# client can re-register
def heartbeat(addr):
    print("Received Heartbeat")

    index = searchEdgeClients(addr)
    if index != -1:
        edge_clients[index]["has_timed_out"] = False

# Registers an edge client as alive. Adds its IP, port and its timed out flag
# to the list of edge clients.
def edgeNodeRegistration(raw_payload):
    registration = edge_pb2.Registration()
    registration.ParseFromString(raw_payload)

    ip = socket.inet_ntop(socket.AF_INET, registration.IP)
    port = registration.port

    edge_clients.append({
        "IP": ip,
        "port": port,
        "has_timed_out": False
    })

    print(f"IP: {ip}")
    print(f"Port: {port}")

def handleRequest(sock, addr):
    parsed_header, raw_payload = net.recv(sock)
    
    match parsed_header.commandID:
        # Schedule task
        case net.Commands.SCHEDULE_TASK:
            scheduleTask(raw_payload)
        # Heartbeat
        case net.Commands.HEARTBEAT:
            heartbeat(addr)
        # Edge node registration
        case net.Commands.REGISTRATION:
            edgeNodeRegistration(raw_payload)

def main():
    removeDeadClients()

    while True:
        sock, addr = server.accept()
        print("Connection accepted")

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