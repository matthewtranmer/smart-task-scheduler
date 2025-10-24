import socket, time, threading, random, json, os, sys, logging
from lib import edge_pb2, net, container

class EdgeClient:
    heartbeat_interval = 30
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, processor_speed: int, logger: logging.Logger, access_server_address: tuple, ip=None, port=0):
        self.access_server_address = access_server_address
        self.logger = logger

        if ip != None:
            self.ip = ip
        else:
            self.ip = net.getLocalIP()

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, port))
        _, self.port = self.server.getsockname()
        self.server.listen()

        logger.info(f"Edge client started on address {self.ip}:{self.port}")

    def serve(self, container_image, container_count, max_container_count, timeout=2):
        self.registerNode()
        self.heartbeatSender()

        try:
            with container.ContainerPool(container_image, container_count, max_container_count) as container_pool:
                while True:
                    sock, addr = self.server.accept()
                    sock.settimeout(timeout)

                    thread = threading.Thread(target=self.handleRequest, args=(sock, addr, container_pool), daemon=True)
                    thread.start()
        except Exception as e:
            logging.ERROR(f"Exception raised in serve function {e}")
            os._exit(-1)

    def setHeartbeatInterval(self, interval_seconds):
        self.heartbeat_interval = interval_seconds

    # Send an still alive signal to the access server. 
    def sendHeartbeat(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(self.access_server_address)

        header = net.createHeader(net.Commands.HEARTBEAT)

        heartbeat = edge_pb2.Heartbeat()
        heartbeat.IP = socket.inet_pton(socket.AF_INET, self.ip)
        heartbeat.port = self.port
        heartbeat_bytes = heartbeat.SerializeToString()

        net.send(client, header, heartbeat_bytes)
        _, response_bytes = net.recv(client)
        
        response = edge_pb2.Response()
        response.ParseFromString(response_bytes)

        print(response)

    # Register the node as alive with the access server
    def registerNode(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(self.access_server_address)
        
        header = net.createHeader(net.Commands.REGISTRATION)

        registration = edge_pb2.Registration()
        registration.IP = socket.inet_pton(socket.AF_INET, self.ip)
        registration.port = self.port
        registration_bytes = registration.SerializeToString()

        net.send(client, header, registration_bytes)
        _, response_bytes = net.recv(client)
        
        response = edge_pb2.Response()
        response.ParseFromString(response_bytes)

        print(response)

    # Run the task on the current node
    def runTask(self, task: edge_pb2.Task, container_pool) -> str:
        print(f"Running task {task.inputID} with id {task.taskID} and input {task.input} on node {self.ip}:{self.port}")

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

            container_params = {"id": task.taskID, "params": task.input.decode(), "inputID": task.inputID}
            json_params = json.dumps(container_params)
            print(f"JSON params: {json_params}")

            start_time = time.perf_counter()
            
            print(f"Container {pool_container.id} sending {json_params}")
            cont.send(json_params.encode())

            received_inputID = -1
            count = 0
            output = ""
            while received_inputID != task.inputID:
                # This call times out and the thread just stops - container still processing input
                try:
                    output, error = cont.receive()
                    if output == "":
                        continue

                    decoded_output = json.loads(output)
                    received_inputID = decoded_output["inputID"]

                    print(f"Container {pool_container.id}, sent input id: {task.inputID}, received input id: {received_inputID}, count {count}, received out: {output}, err: {error}")
                    count += 1
                except TimeoutError:
                    return net.createResponse(False, b"Container timed out")

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

            return net.createResponse(True, output.encode())

    def handleRequest(self, sock, addr, container_pool):
        parsed_header, raw_payload = net.recv(sock)   

        response = None
        if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
            task = edge_pb2.Task()
            task.ParseFromString(raw_payload)

            response = self.runTask(task, container_pool)

        if response == None:
            response = net.createResponse(False, b"Command does not exist")

        header = net.createHeader(parsed_header.commandID)
        net.send(sock, header, response.SerializeToString())

    # Function that sends a heartbeat to the access server every heartbeat_interval
    # seconds.
    def heartbeatSender(self):
        self.sendHeartbeat()
        print("sent heartbeat!")

        threading.Timer(self.heartbeat_interval, self.heartbeatSender).start()

def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    access_server_address = ("10.45.1.34", 2004)

    edge_client = EdgeClient(
        processor_speed=3_400_000_000_000,
        logger=logger,
        access_server_address=access_server_address
    )

    edge_client.serve("task_sandbox", 1, 999)

if __name__ == "__main__":
    main()


