import socket, time, threading, random, json, os, sys, logging
from lib import edge_pb2, net, container, system

class CloudClient:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #TODO: CLOUD CLIENT DOESN'T NEED MEMORY AND CPUs
    def __init__(
            self,
            logger: logging.Logger, 
            ip=None, 
            port=0
        ):
        self.logger = logger

        if ip != None:
            self.ip = ip
        else:
            self.ip = net.getLocalIP()

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, port))
        _, self.port = self.server.getsockname()
        self.server.listen()

        logger.info(f"Cloud client started on address {self.ip}:{self.port}")

    def serve(self, container_image, timeout=5):
        try:
            cpus = system.getPhysicalCpuIds()

            with container.StaticContainerPool(container_image, cpus) as container_pool:
                while True:
                    sock, addr = self.server.accept()
                    sock.settimeout(timeout)

                    thread = threading.Thread(target=self.handleRequest, args=(sock, addr, container_pool), daemon=True)
                    thread.start()
        except Exception as e:
            logging.ERROR(f"Exception raised in serve function {e}")
            os._exit(-1)


    # Run the task on the current node
    def runTask(self, task: edge_pb2.Task, container_pool) -> str:
        print(f"Running task {task.inputID} with id {task.taskID} and input {task.input[:100]} on node {self.ip}:{self.port}")

        try:
            with container_pool.getContainer() as pool_container:
                print("Scheduling....")
                cont = pool_container.container

                container_params = {"id": task.taskID, "params": task.input.decode(), "inputID": task.inputID}
                json_params = json.dumps(container_params)

                start_time = time.perf_counter()
                
                print(f"Container {pool_container.id} sending {json_params[:100]}")
                cont.send(json_params.encode())

                received_inputID = -1
                count = 0
                output = ""
                while received_inputID != task.inputID:
                    # This call times out and the thread just stops - container still processing input
                    # TODO: too much indentation, handle errors in container
                    try:
                        output, error = cont.receive()
                        if output == "":
                            continue

                        if (error):
                            while output != "":
                                print(f"{output}")
                                output, error = cont.receive()
                            return net.createResponse(False, b"Container error")

                        print(f"OUTPUT: {output}")

                        decoded_output = json.loads(output)
                        received_inputID = decoded_output["inputID"]

                        print(f"Container {pool_container.id}, sent input id: {task.inputID}, received input id: {received_inputID}, count {count}, received out: {output}, err: {error}")
                        count += 1
                    except TimeoutError:
                        print("CONTAINER TIMED OUT!!")
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
            
        except container.NoContainersExeception:
            return net.createResponse(False, "No containers available")


    def handleRequest(self, sock, addr, container_pool):
        parsed_header, raw_payload = net.recv(sock)   

        response = b""
        if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
            task = edge_pb2.Task()
            task.ParseFromString(raw_payload)

            response = self.runTask(task, container_pool)

        else:
            response = net.createResponse(False, b"Command does not exist")

        header = net.createHeader(parsed_header.commandID)
        net.send(sock, header, response.SerializeToString())

class EdgeClient(CloudClient):
    heartbeat_interval = 30

    def __init__(
            self, 
            logger,
            access_server_address: tuple, 
            cpus: int = None,
            memory_mb: int = None,
            ip=None, 
            port=0
        ):
        super().__init__(logger, ip, port)

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

        if cpus != None:
            self.cpus = cpus
        else:
            self.cpus = len(system.getPhysicalCpuIds())

        if memory_mb != None:
            self.memory_mb = memory_mb
        else:
            # Leave 1024 MiB available for system use
            self.memory_mb = system.getSystemMemoryMB() - 1024

        logger.info(f"Edge client started on address {self.ip}:{self.port} with {self.cpus} cpus and {self.memory_mb}MB of memory")

    def serve(self, container_image, timeout=5):
        self.registerNode()
        self.heartbeatSender()

        super().serve(container_image, timeout)

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

        # Re-register node if not registered
        if (not response.success and response.value == b"Edge node does not exist!"):
            self.registerNode()

        print(response)

    # Register the node as alive with the access server
    def registerNode(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(self.access_server_address)
        
        header = net.createHeader(net.Commands.REGISTRATION)

        registration = edge_pb2.Registration()
        registration.IP = socket.inet_pton(socket.AF_INET, self.ip)
        registration.port = self.port
        registration.cpus = len(system.getPhysicalCpuIds())
        registration.memory_mb = system.getSystemMemoryMB()

        registration_bytes = registration.SerializeToString()

        net.send(client, header, registration_bytes)
        _, response_bytes = net.recv(client)
        
        response = edge_pb2.Response()
        response.ParseFromString(response_bytes)

    # Function that sends a heartbeat to the access server every heartbeat_interval
    # seconds.
    def heartbeatSender(self):
        self.sendHeartbeat()
        print("sent heartbeat!")

        threading.Timer(self.heartbeat_interval, self.heartbeatSender).start()

