import socket, threading, os, sys, logging
from lib import edge_pb2, net, container, system

class EdgeClient:
    heartbeat_interval = 5

    def __init__(
            self,
            logger: logging.Logger, 
            access_server_address: tuple, 
            cpus: int = None,
            clock_speed_cps: int = None,
            memory_mb: int = None,
            ip=None, 
            port=0
        ):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.access_server_address = access_server_address
        self.logger = logger

        if cpus != None:
            self.cpus = cpus
        else:
            self.cpus = len(system.getPhysicalCpuIds())

        if clock_speed_cps != None:
            self.clock_speed_cps = clock_speed_cps
        else:
            self.clock_speed_cps = system.getClockSpeedCPS()

        if memory_mb != None:
            self.memory_mb = memory_mb
        else:
            # Leave 1024 MiB available for system use
            self.memory_mb = system.getSystemMemoryMB() - 1024

        if ip != None:
            self.ip = ip
        else:
            self.ip = net.getLocalIP()

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, port))
        _, self.port = self.server.getsockname()
        self.server.listen()

        logger.info(f"Edge client started on address {self.ip}:{self.port} with {self.cpus} cpus at {self.clock_speed_cps / 1000**2}MHz and {self.memory_mb}MB of memory")

    def serve(self, container_image, timeout=5):
        self.registerNode()
        self.heartbeatSender()

        try:
            total_cpus = system.getPhysicalCpuIds()
            allowed_cpus = total_cpus[:self.cpus]

            with container.StaticContainerPool(container_image, allowed_cpus) as container_pool:
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
        registration.cpus = self.cpus
        registration.memory_mb = self.memory_mb
        registration.clock_speed_cps = self.clock_speed_cps

        registration_bytes = registration.SerializeToString()

        net.send(client, header, registration_bytes)
        _, response_bytes = net.recv(client)
        
        response = edge_pb2.Response()
        response.ParseFromString(response_bytes)

    # Run the task on the current node
    def runTask(self, task: edge_pb2.Task, container_pool) -> edge_pb2.Response:
        # Get a container from the pool
        try:
            with container_pool.getContainer() as pool_container:
                scheduled_container = pool_container.container
                
                try:
                    response = scheduled_container.executeTask(task)
                    self.logger.info(f"Executed task with id {task.taskID}, processing time {response.processing_time_ms}ms, deadline {task.deadline_ms}ms")

                    if (response.error):
                        self.logger.warning(f"Received error while processing task with id {task.taskID}")
                        self.logger.warning(response.traceback)
                        return net.createResponse(False, response.traceback.encode())

                    return net.createResponse(True, response.value)

                except container.InternalContainerError as e:
                    self.logger.error(f"Error response while executing task with ID {task.taskID}")
                    self.logger.exception(e)
                    return net.createResponse(False, b"Internal container error encountered while executing task")
                
                except TimeoutError:
                    return net.createResponse(False, b"Container timeout while executing task")
        
        except container.NoContainersExeception:   
            return net.createResponse(False, b"No containers available")

    def scheduleTask(self, payload, container_pool):
        task = edge_pb2.Task()
        task.ParseFromString(payload)

        try:
            logging.info(f"Received task with ID: {task.taskID}")
            return self.runTask(task, container_pool)
        
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

    # Function that sends a heartbeat to the access server every heartbeat_interval
    # seconds.
    def heartbeatSender(self):
        try:
            self.sendHeartbeat()
            print("sent heartbeat!")

        except Exception as e:
            self.logger.exception(e)

        threading.Timer(self.heartbeat_interval, self.heartbeatSender).start()

def main(address, cpus, memory):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if address == None:
        access_server_address = ("10.45.1.34", 2004)
    else:
        access_server_address = address    

    logger = logging.getLogger(__name__)

    edge_client = EdgeClient(
        logger=logger,
        access_server_address=access_server_address,
        cpus=cpus,
        clock_speed_cps=system.getClockSpeedCPS(),
        memory_mb=memory
    )

    edge_client.serve("task_sandbox", timeout=5)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: [AS_ADDRESS]:[AS_PORT] [CPUs] [MEMORY(MB)]")
        os._exit(-1)


    address = None
    if len(sys.argv) > 1:
        address = sys.argv[1]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    cpus = None
    memory = None

    if len(sys.argv) > 3:
        cpus = int(sys.argv[2])
        memory = int(sys.argv[3])

    main(address, cpus, memory)