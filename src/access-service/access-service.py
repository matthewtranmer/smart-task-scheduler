import socket, threading, logging, traceback, time, json
from lib import edge_pb2, net
from lib import scheduler as s
from diagnostics import Diagnostics

    
class EdgeAccess:
    heartbeat_timeout_s = 30
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, scheduler: s.Scheduler, logger, diagnostics, cloud_address, ip=None, port=2004):
        self.scheduler = scheduler
        self.logger = logger
        self.diagnostics = diagnostics
        self.port = port
        self.cloud_address = (socket.gethostbyname(cloud_address[0]), cloud_address[1])

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

    def gatherDiagnostics(self):
        data = self.diagnostics.sampleAllDiagnosticData()
        json_data = json.dumps(data)

        return net.createResponse(True, json_data.encode()).SerializeToString()


    # Scan through all edge clients. If the client has timed out flag set to true then 
    # remove it from the clients list. If the client hasn't timed out, set the flag so 
    # that it has timed out. The heartbeat function will reset the flag so that it is 
    # not removed on the next pass.
    # Reinvoked asynchronously every heartbeat_timeout_s
    def removeDeadClients(self):
        self.scheduler.removeDeadNodes()

        threading.Timer(self.heartbeat_timeout_s, self.removeDeadClients).start()

    #Returns true on deadline hit, false on deadline miss
    def calculateDeadlineHit(self, raw_payload, processing_time, diagnostics) -> bool:
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        if (processing_time * 1000 < task.deadline_ms):
            diagnostics.addDeadlineTask(True)
            return True
        
        diagnostics.addDeadlineTask(False)
        return False
    

    # Called when a task is submitted to the access server by a client.
    def scheduleTask(self, header, raw_payload, diagnostics, timeout=5):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)
        memory_mb = task.memory_requirement_mb

        processing_time = 0

        # Try again at most 100 times if a node isn't responding
        for _ in range(100):
            scheduled_on_edge = True

            try:
                # raise s.NoNodesExeception  # TODO: remove this line when scheduler is ready
                address = self.scheduler.schedule(memory_mb=memory_mb)
                self.logger.debug(f"Scheduled task on node {address}")
            # except s.NoNodesExeception:
                # return net.createResponse(False, b"There are no available clients to perform the task").SerializeToString()
            # except s.NodeResourceExecpetion as e:
                # return net.createResponse(False, e.__str__().encode()).SerializeToString()
            except (s.NoNodesExeception, s.NodeResourceExecpetion):
                address = self.cloud_address
                scheduled_on_edge = False
                self.logger.debug(f"Sent task to cloud")

            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if (scheduled_on_edge):
                connection.settimeout(timeout)
            else:
                connection.settimeout(timeout*2.5)

            ip = address[0]
            port = address[1]

            try:
                connection.connect((ip, port))
                break
            except (ConnectionRefusedError, TimeoutError):
                if scheduled_on_edge:
                    self.logger.warning(f"Node {ip}:{port} is not responding! Removing from registry")

                    self.scheduler.removeNode(address)
                else:
                    self.logger.error(f"Cloud service at {ip}:{port} is not responding!")
                    return net.createResponse(False, b"Cloud service offline!").SerializeToString()

            except Exception:
                traceback.print_exc()

        try:
            start = time.perf_counter()
            net.send(connection, header, raw_payload)
            
            _, response = net.recv(connection)
            end = time.perf_counter()

            processing_time = end - start

            diagnostics.incrementProcessingTime(processing_time, task.taskID)
            deadline_hit = self.calculateDeadlineHit(raw_payload, processing_time, diagnostics)
            
            #TODO: make work with cloud nodes -----------------------------------------
            #self.diagnostics.addJob(task.taskID, (ip, port), processing_time*1000, task.deadline_ms, deadline_hit)

            return response
        except TimeoutError:
            return net.createResponse(False, b"Node timedout").SerializeToString()
        finally:
            connection.close()

            if scheduled_on_edge:
                self.scheduler.resetNode(address, memory_mb, processing_time*1000)

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
            case net.Commands.GATHER_DIAGNOSTICS:
                response = self.gatherDiagnostics()

        header = net.createHeader(parsed_header.commandID)
        net.send(sock, header, response)


def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    scheduler = s.RoundRobinWithAllocation()
    logger = logging.getLogger(__name__)
    
    diagnostics = Diagnostics(
        measurement_interval_s=4,
        scheduler=scheduler, 
        display=True
    )

    access_server = EdgeAccess(
        scheduler=scheduler,
        logger= logger,
        diagnostics=diagnostics,
        # cloud_address=("10.45.1.34", 16225)
        cloud_address=("ec2-51-21-247-208.eu-north-1.compute.amazonaws.com", 16225)
    )

    access_server.serve()    

if __name__ == "__main__":
    main()








