import socket, time, threading, random, json, os, sys, logging
from lib import edge_pb2, net, container, system
import queue, asyncio

class CloudClient:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    waiting_tasks = 0
    waiting_lock = threading.Lock()

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
        self.timeout = timeout

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
    async def runTask(self, task: edge_pb2.Task, container_pool, blocking=True) -> str:
        if (blocking):
            with self.waiting_lock:
                self.waiting_tasks += 1

        # Get a container from the pool
        with await container_pool.getContainer(blocking) as pool_container:
            if (blocking):
                with self.waiting_lock:
                    self.waiting_tasks -= 1
            
            scheduled_container = pool_container.container

            print(f"Waiting tasks: {self.waiting_tasks}")
            
            try:
                response, processing_time = scheduled_container.executeTask(task)
                self.logger.info(f"Executed task with id {task.taskID}, processing time {processing_time}ms")

                return net.createResponse(True, response.encode())

            except container.InternalContainerError as e:
                self.logger.exception(e)
                return net.createResponse(False, b"Internal container error encountered while executing task")
            
            except TimeoutError:
                return net.createResponse(False, b"Container timeout while executing task")
            
        return net.createResponse(False, b"No containers available")
                
    def scheduleTask(self, payload, container_pool):
        task = edge_pb2.Task()
        task.ParseFromString(payload)

        try:
            logging.debug("Running task")

            response = self.runTask(task, container_pool)
            return asyncio.run(asyncio.wait_for(response, timeout=self.timeout))
        
        except asyncio.TimeoutError:
            logging.warning("Timed out waiting for a container")
            return net.createResponse(False, b"Timed out waiting for a container")
        
        except container.NoContainersExeception:
            logging.warning("No containers")
            return net.createResponse(False, b"No containers")

    def handleRequest(self, sock, addr, container_pool):
        parsed_header, raw_payload = net.recv(sock)   

        response = b""
        if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
            response = self.scheduleTask(raw_payload, container_pool)

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

    def runTask(self, task, container_pool):
        return super().runTask(task, container_pool, blocking=False)

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

