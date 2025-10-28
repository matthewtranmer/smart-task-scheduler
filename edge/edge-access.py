import socket, threading, logging, traceback, time
from lib import edge_pb2, net
from lib import scheduler as s

class Diagnostics:
    measurement_interval_s = 0

    task_count = 0
    tasks_per_second = 0

    processing_times = 0
    processing_times_count = 0
    average_processing_time = 0

    deadline_hit_rate = 0
    deadline_misses = 0
    deadline_hits = 0

    def __init__(self, measurement_interval_s, display=False):
        self.display = display
        self.measurement_interval_s = measurement_interval_s
        self._mainLoop()

    def _mainLoop(self):
        self._calculateAverageProcessingTimes()
        self._calculateTasksPerSecond()
        self._calculateDeadlineHitRate()
        
        threading.Timer(self.measurement_interval_s, self._mainLoop).start()

    def _calculateDeadlineHitRate(self):
        task_count = self.deadline_misses + self.deadline_hits
        if task_count == 0:
            self.deadline_hit_rate = 0
        else:
            self.deadline_hit_rate = round((self.deadline_hits / task_count) * 100, 3)

        self.deadline_hits = 0
        self.deadline_misses = 0

        if (self.display):
            print(f"Deadline hit rate: {self.deadline_hit_rate}%")

    def _calculateAverageProcessingTimes(self):
        if (self.processing_times_count == 0):
            self.average_processing_time = 0
        else:
            self.average_processing_time = round(self.processing_times / self.processing_times_count, 3)
        
        self.processing_times = 0
        self.processing_times_count = 0

        if (self.display):
            print(f"Average processing time: {self.average_processing_time}")

    # Called every task_measurement_interval_s
    def _calculateTasksPerSecond(self):
        self.tasks_per_second = round(self.task_count / self.measurement_interval_s, 3)
        self.task_count = 0

        if (self.display):
            print(f"Tasks per second: {self.tasks_per_second}")

    def incrementTasks(self, count=1):
        self.task_count += count

    def tasksPerSecond(self) -> int:
        return self.tasks_per_second
    
    def incrementProcessingTime(self, processing_time):
        self.processing_times += processing_time
        self.processing_times_count += 1

    def addDeadlineTask(self, did_hit_deadline: bool):
        if (did_hit_deadline):
            self.deadline_hits += 1
        else:
            self.deadline_misses += 1
    
class EdgeAccess:
    heartbeat_timeout_s = 30
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, scheduler: s.Scheduler, logger, diagnostics, ip=None, port=2004):
        self.scheduler = scheduler
        self.logger = logger
        self.diagnostics = diagnostics
        self.port = port

        if ip != None:
            self.ip = ip
        else:
            self.ip = net.getLocalIP()

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))

        self.server.listen()

    def serve(self, timeout=2):
        self.removeDeadClients()

        self.logger.info(f"Starting access server on address {self.ip}:{self.port}")

        while True:
            sock, addr = self.server.accept()
            sock.settimeout(timeout)

            threading.Thread(target=self.handleRequest, args=(sock, addr)).start()

    # Scan through all edge clients. If the client has timed out flag set to true then 
    # remove it from the clients list. If the client hasn't timed out, set the flag so 
    # that it has timed out. The heartbeat function will reset the flag so that it is 
    # not removed on the next pass.
    # Reinvoked asynchronously every heartbeat_timeout_s
    def removeDeadClients(self):
        self.scheduler.removeDeadNodes()

        threading.Timer(self.heartbeat_timeout_s, self.removeDeadClients).start()

    def calculateDeadlineHit(self,raw_payload, processing_time, diagnostics):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        if (processing_time * 1000 < task.deadline_ms):
            diagnostics.addDeadlineTask(True)
        else:
            diagnostics.addDeadlineTask(False)

    # Called when a task is submitted to the access server by a client.
    def scheduleTask(self, header, raw_payload, diagnostics):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)
        memory_mb = task.memory_requirement_mb

        for _ in range(100):
            try:
                edge_address = self.scheduler.schedule(memory_mb=memory_mb)
            except s.NoNodesExeception:
                return net.createResponse(False, b"There are no available clients to perform the task").SerializeToString()
            except s.NodeResourceExecpetion as e:
                return net.createResponse(False, e.__str__().encode()).SerializeToString()

            self.logger.debug(f"Scheduled task on node {edge_address}")

            edge_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            edge_connection.settimeout(3)

            ip = edge_address[0]
            port = edge_address[1]

            try:
                edge_connection.connect((ip, port))
                break
            except (ConnectionRefusedError, TimeoutError):
                self.logger.warning(f"Node {ip}:{port} is not responding! Removing from registry")

                # TODO: Unsafe - node could be removed by other routine checking for heartbeats
                # during critical section
                self.scheduler.removeNode(edge_address)
            except Exception as e:
                traceback.print_exc()

        try:
            start = time.perf_counter()
            net.send(edge_connection, header, raw_payload)
            
            _, response = net.recv(edge_connection)
            end = time.perf_counter()

            processing_time = end - start

            diagnostics.incrementProcessingTime(processing_time)
            self.calculateDeadlineHit(raw_payload, processing_time, diagnostics)

            return response
        except TimeoutError:
            return net.createResponse(False, b"Edge node timedout").SerializeToString()
        finally:
            self.scheduler.resetNode(edge_address, memory_mb)

    # Called when an edge client sends a heartbeat signal. Sets the client's 
    # has timed out flag to false. 
    def heartbeat(self,raw_payload):
        heartbeat_payload = edge_pb2.Heartbeat()
        heartbeat_payload.ParseFromString(raw_payload)

        ip = socket.inet_ntop(socket.AF_INET, heartbeat_payload.IP)
        port = heartbeat_payload.port

        self.logger.info(f"Received heartbeat from {ip}:{port}")

        # index = self.searchEdgeClients((ip, port))
        # if index != -1:
        #     self.edge_clients[index]["has_timed_out"] = False
            
        #     return net.createResponse(True, b"Success").SerializeToString()
        
        try:
            self.scheduler.nodeHeartbeat((ip, port))
            return net.createResponse(True, b"Success").SerializeToString()
        except KeyError:
            return net.createResponse(False, b"Edge node does not exist!").SerializeToString()

    # Registers an edge client as alive. Adds its IP, port and its timed out flag
    # to the list of edge clients.
    def edgeNodeRegistration(self, raw_payload):
        registration = edge_pb2.Registration()
        registration.ParseFromString(raw_payload)

        ip = socket.inet_ntop(socket.AF_INET, registration.IP)
        port = registration.port

        added_node = self.scheduler.addNode((ip, port), registration.cpus, registration.memory_mb)
        if not added_node:
            return net.createResponse(False, b"Client already exists in the registry!")

        self.logger.info(f"Regstering node {ip}:{port}")

        return net.createResponse(True, b"Success").SerializeToString()

    def handleRequest(self, sock, addr):
        parsed_header, raw_payload = net.recv(sock)
        response = b""

        match parsed_header.commandID:
            # Schedule task
            case net.Commands.SCHEDULE_TASK:
                response = self.scheduleTask(parsed_header, raw_payload, self.diagnostics)
                self.diagnostics.incrementTasks()
            # Heartbeat
            case net.Commands.HEARTBEAT:
                response = self.heartbeat(raw_payload)
            # Edge node registration
            case net.Commands.REGISTRATION:
                response = self.edgeNodeRegistration(raw_payload)

        header = net.createHeader(parsed_header.commandID)
        net.send(sock, header, response)


def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    scheduler = s.RoundRobinWithAllocation()
    logger = logging.getLogger(__name__)
    diagnostics = Diagnostics(4, True)

    access_server = EdgeAccess(
        scheduler=scheduler,
        logger= logger,
        diagnostics=diagnostics
    )

    access_server.serve()    

if __name__ == "__main__":
    main()








