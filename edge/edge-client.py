import socket, time, threading, random, json
from lib import edge_pb2, net, container

PROCESSOR_SPEED = 3_400_000_000_000 #3.4GHz

task_parameters = [
    {
        "image": "addition",
        "CPU_time_ms": 312
    }
]

heartbeat_interval = 30

ip = net.getLocalIP()
access_server_address = ("10.45.1.34", 2004)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((ip, 0))

_, port = server.getsockname()
server.listen()

print(f"Edge client started on address {ip}:{port}")

# Send an still alive signal to the access server. 
def sendHeartbeat():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(access_server_address)

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
    client.connect(access_server_address)
    
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
def runTask(task: edge_pb2.Task, container_pool) -> str:
    print(f"Running task with id {task.taskID} and input {task.input} on node {ip}:{port}")

    # cpu_time = task_parameters[task.taskID]["CPU_time_ms"]
    # image = task_parameters[task.taskID]["image"]

    # if (task.deadline_ms > cpu_time * 2.5):
    #     adjusted_deadline_ms = task.deadline_ms * 0.8
    #     adjusted_cpu_time = cpu_time * 1.5

    #     if (adjusted_cpu_time > adjusted_deadline_ms):
    #         adjusted_cpu_time = adjusted_deadline_ms

    #     print(f"Scheduling task with throttling - CPU_time: {adjusted_cpu_time}, deadline: {adjusted_deadline_ms}")
    #     print("Not implemented...")
    #     # cont = container.Container(
    #     #     image,
    #     #     adjusted_deadline_ms,
    #     #     adjusted_cpu_time
    #     # )
    # else:
    #     print("Scheduling task normally")
    #     # cont = container.Container(image)

    with container_pool.getContainer() as pool_container:
        print("Scheduling....")
        cont = pool_container.container

        input_id = str(random.randint(0,99999999999999999))

        container_params = {"id": task.taskID, "params": task.input.decode(), "input_id": input_id}
        json_params = json.dumps(container_params)
        print(f"JSON params: {json_params}")

        start_time = time.perf_counter()
        
        print(f"Container {pool_container.id} sending {json_params}")
        cont.send(json_params.encode())

        count = 0
        output = ""
        while output == "":
            output, error = cont.receive()
            print(f"Container {pool_container.id} count {count}, received out: {output}, err: {error}")
            count += 1

        end_time = time.perf_counter()

        print(f"Output length: {len(output)}")

        execution_time_ms = (end_time - start_time) * 1000

        if (error):
            print("Error running container")
            while len(output) > 0:
                output, error = cont.receive()
                print(output) 
        else:
            print(f"Response generated as: {output}")
            print(f"Execution time: {execution_time_ms}ms")
            print(f"Deadline: {task.deadline_ms}ms")
            print("")

        
        

        return output, input_id

def handleRequest(sock, addr, container_pool):
    parsed_header, raw_payload = net.recv(sock)   
    response_value = b"" 

    if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        response_value, INPUT_ID = runTask(task, container_pool)

    if (response_value != ""):
        response = net.createResponse(True, response_value.encode())
    else:
        print("err")
        response = net.createResponse(False, b"Error running task" + str(INPUT_ID).encode())

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

    try:
        with container.ContainerPool("task_sandbox", 1, 50) as container_pool:
            while True:
                sock, addr = server.accept()
                sock.settimeout(2)

                thread = threading.Thread(target=handleRequest, args=(sock, addr, container_pool), daemon=True)
                thread.start()
    except Exception:
        print("test")

if __name__ == "__main__":
    main()

