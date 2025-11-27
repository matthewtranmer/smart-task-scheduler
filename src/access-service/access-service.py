import random
import socket, threading, logging, traceback, time, json
from lib import edge_pb2, net
from lib import scheduler as s
from diagnostics import Diagnostics

    
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
    def calculateDeadlineHit(self, raw_payload, processing_time_ms, diagnostics) -> bool:
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        if (processing_time_ms < task.deadline_ms):
            diagnostics.addDeadlineTask(True)
            return True
        
        diagnostics.addDeadlineTask(False)
        return False
    
    # Called when a task is submitted to the access server by a client.
    def scheduleTask(self, header, raw_payload, diagnostics, edge_timeout=5):
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)
        task.inputID = random.randint(1000000000,2147483640)

        # Attempt to make a connection to a node at most 3 times
        for i in range(3):
            # Schedule either an edge or cloud node
            scheduled_node = self.scheduler.schedule(task.memory_requirement_mb)
        
            # Try to connect to remote node
            try:
                remote_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_connection.settimeout(2)
                remote_connection.connect(scheduled_node.address)

            # Node is not alive - remove from registry
            except (ConnectionRefusedError, TimeoutError):
                if scheduled_node.node_type == s.NodeType.CLOUD:
                    self.logger.warning(f"Cloud service at {scheduled_node.address} is not responding!")
                else:
                    self.logger.warning(f"Node {scheduled_node.address} is not responding! Removing from registry")
                
                self.scheduler.removeNode(scheduled_node)
                continue

            # Increase timeout for tasks scheduled on the cloud
            if scheduled_node.node_type == s.NodeType.CLOUD:
                self.logger.debug("Scheduled task on the cloud")
                remote_connection.settimeout(edge_timeout * 2)
            else:
                self.logger.debug(f"Scheduled task on the edge node {scheduled_node.address}")
                remote_connection.settimeout(edge_timeout)

            # Start the processing time timer
            start = time.perf_counter()

            # Attempt to schedule the task on the remote node
            try:
                net.send(remote_connection, header, task.SerializeToString())
                _, response = net.recv(remote_connection)
            
            # Node timed out - attempt to schedule another node
            except TimeoutError:
                logging.warning(f"Remote node {scheduled_node.address} timed out during task execution - attempting to reschedule")
                continue

            # Connection reset by node - attempt to schedule another node
            except ConnectionResetError:
                logging.warning(f"Remote node {scheduled_node.address} reset connection - attempting to reschedule")
                continue

            # Broken pipe error - attempt to schedule another node
            except BrokenPipeError:
                logging.warning(f"Remote node {scheduled_node.address} - broken pipe error - attempting to reschedule")
                continue

            finally:
                remote_connection.close()

                # Stop the processing time timer
                end = time.perf_counter()

                # Calculate the processing time in ms
                processing_time = (end - start) * 1000
                
                # Reset the scheduled node
                self.scheduler.resetNode(scheduled_node, processing_time)

            # Log diagnostic information
            diagnostics.incrementProcessingTime(processing_time, task.taskID)
            deadline_hit = self.calculateDeadlineHit(raw_payload, processing_time, diagnostics)
            #TODO: make work with cloud nodes -----------------------------------------
            self.diagnostics.addJob(task.taskID, scheduled_node.address, processing_time, task.deadline_ms, deadline_hit)

            self.diagnostics.incrementTasks()

            # Forward the raw response received from the remote node
            return response
        
        # Couldn't find an edge or cloud node in 3 attempts
        return net.createResponse(False, b"Could not find an available node to schedule the task").SerializeToString()

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
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # cloud_ip = "LB1-6c7327e45f7a7b95.elb.eu-north-1.amazonaws.com"
    # cloud_ip = socket.gethostbyname(cloud_ip)
    # cloud_port = 8000
    # cloud_address = (cloud_ip, cloud_port)
    cloud_address = ("127.0.0.1", 16225)
    
    scheduler = s.RoundRobinEdgeCloud(cloud_address)
    logger = logging.getLogger(__name__)
    
    diagnostics = Diagnostics(
        measurement_interval_s=20,
        scheduler=scheduler, 
        display=True
    )

    access_server = EdgeAccess(
        scheduler=scheduler,
        logger= logger,
        diagnostics=diagnostics
    )

    access_server.serve()    

if __name__ == "__main__":
    main()








