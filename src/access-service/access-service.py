import random
import socket, threading, logging, traceback, time, json
from lib import dependency_graph_definitions, edge_pb2, net, dagtask, task_definitions
from lib import scheduler as s
from diagnostics import Diagnostics
from dataclasses import dataclass

@dataclass
class TaskInformation:
    # The actual task to be scheduled
    task: edge_pb2.Task

    # Where the response needs to be sent
    client_socket: socket.socket


class PriorityTaskQueue:
    def __init__(self):
        self.queue: list[TaskInformation] = []

    # Insert tasks into the queue based on their deadline
    def add_task(self, new_task: TaskInformation):
        for i in range(len(self.queue)):
            if self.queue[i].task.deadline_ms > new_task.task.deadline_ms:
                self.queue.insert(i, new_task)
                return
            
        self.queue.append(new_task)

    def flush_queue(self):
        new_queue: list[TaskInformation] = []

        # Create a new queue with the task information from this time step
        for task in self.queue:
            new_queue.append(task)

        # Remove the items from the global queue that have been added to the 
        # new queue.
        # Done this way for thread safety 
        for task in new_queue:
            self.queue.remove(task)

        return new_queue

    
class EdgeAccess:
    heartbeat_timeout_s = 8

    def __init__(
            self, 
            scheduler: s.Scheduler, 
            queue_wait_time_s: int, 
            priority_task_threshold_s: int,
            logger: logging.Logger, 
            diagnostics, 
            ip=None, 
            port=2004
        ):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.task_queue = PriorityTaskQueue()

        self.scheduler = scheduler
        self.queue_wait_time_s = queue_wait_time_s
        self.priority_task_threshold_s = priority_task_threshold_s
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
        # Init periodic function
        self.removeDeadClients()
        self.flush_task_queue_and_execute()

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
        dead_nodes = self.scheduler.removeDeadNodes()

        if len(dead_nodes) > 0:
            self.logger.warning(f"Removed dead nodes: {dead_nodes}")


        threading.Timer(self.heartbeat_timeout_s, self.removeDeadClients).start()

    # Method that takes the incoming task request from the client.
    # It either queues it or sends it for execution staight away.
    def handle_task(self, incoming_request, client_socket):
        _, raw_payload = incoming_request

        # Create the task object
        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)
        task.inputID = random.randint(1000000000, 2147483640)

        self.logger.debug(f"Received task with taskID: {task.taskID} from client")

        # Populate task resource parameters if not a parallel task
        if task.taskID not in dependency_graph_definitions.parallel_task_IDs:
            print(f"Task is not a parallel task")
            parameters: task_definitions.TaskParameters = task_definitions.task_parameters[task.taskID]

            task.cycles_required = parameters.cycles
            task.memory_requirement_mb = parameters.memory_mb

        task_info = TaskInformation(task, client_socket)

        # If task deadline greater than threshold, add task to queue
        if (task.deadline_ms / 1000 > self.priority_task_threshold_s):
            self.logger.debug("Adding task to queue")
            self.task_queue.add_task(task_info)
        else:
            self.logger.info("Priority task detected, fast tracking scheduling...")
            self.execute_task()
            threading.Thread(target=self.execute_normal_task, args=(task_info, )).start()

    # Called every queue_wait_time_s seconds
    # Flushes the task queue; sceduling each task
    def flush_task_queue_and_execute(self):
        queue: list[TaskInformation] = self.task_queue.flush_queue()

        for task_info in queue:
            self.logger.debug(f"Flushing taskID: {task_info.task.taskID} from the queue")
            self.execute_task(task_info)

        # Recall function after delay
        threading.Timer(self.queue_wait_time_s, self.flush_task_queue_and_execute).start()

    # Method that sends a task to an edge node and handles any errors
    def handle_task_offload(self, task: edge_pb2.Task) -> tuple[bytes, bool]:
        self.logger.info(f"Executing task with ID {task.taskID} and deadline {task.deadline_ms}")

        success = False
        # Send the task to a node
        try:
            response = self.send_to_node(task)
            success = True
        except s.NoNodesExeception as e:
            response = net.createResponse(False, e.message.encode(), response_code=500).SerializeToString()
        except s.TaskDroppedExeception as e:
            response = net.createResponse(False, e.message.encode(), response_code=551).SerializeToString()

        return response, success

    # Executes a task from task information, deciding wether it is a sub task or normal task.
    def execute_task(self, task_info: TaskInformation):
        # Test to see if task is a DAG task
        if task_info.task.taskID in dependency_graph_definitions.dag_tasks:

            task_graph_class: type[dagtask.TaskDependencyGraph] = dependency_graph_definitions.get_dag_task_implementation(task_info.task.taskID)
            
            task_graph: dagtask.TaskDependencyGraph = task_graph_class(
                deadline_s=task_info.task.deadline_ms / 1000 # Convert to seconds
            )

            # Get the inital tasks from the DAG that have no dependencies
            start_tasks, nodes = task_graph.get_start_tasks(task_info.task.input)
            self.logger.debug(f"Start tasks length: {len(start_tasks)}")

            assert len(start_tasks) == len(nodes)

            # Execute each task
            for i in range(len(start_tasks)):
                threading.Thread(target=self.execute_sub_task, args=(start_tasks[i], task_graph, task_info.client_socket, nodes[i])).start()

        # Normal task
        else:
            threading.Thread(target=self.execute_normal_task, args=(task_info.task, task_info.client_socket)).start()


    # Method that handles execution of tasks within a DAG task
    def execute_sub_task(
            self, 
            task: edge_pb2.Task,
            task_graph: dagtask.TaskDependencyGraph, 
            client_socket: socket.socket,
            graph_node_ID: int
            ):
        
        print(f"Executing subtask with ID {task.taskID}, deadline {task.deadline_ms} and input {task.input[:50]}")

        # Execute task
        raw_response, success = self.handle_task_offload(task)

        if not success:
            # TODO: handle task failures    
            raise Exception("Error in sub task")
        
        print("Subtask executed sucessfully - now update graph state")
        
        response = edge_pb2.Response()
        response.ParseFromString(raw_response)

        # Return the tasks that can now execute after the dependency completion
        new_tasks, new_task_nodes, finished = task_graph.update_state(
            completed_node_id=graph_node_ID,
            result=response.value
        )

        if finished:
            final_result = task_graph.final_result
            print(f"RECEIVED FINAL RESULT: {final_result}")

            response = net.createResponse(True, final_result, response_code=200).SerializeToString()

            # Return the response to the remote client
            header = net.createHeader(net.Commands.SCHEDULE_TASK)
            net.send(client_socket, header, response)

        # Ensure the two returned lists are the same length
        assert len(new_tasks) == len(new_task_nodes)
        for i in range(len(new_tasks)):
            threading.Thread(target=self.execute_sub_task, args=(new_tasks[i], task_graph, client_socket, new_task_nodes[i])).start()

    # Method that handles execution of tasks within a DAG task
    # Executed in separate threads
    def execute_normal_task(self, task: edge_pb2.Task, client_socket: socket.socket):
        # Offload task to compute
        response, _ = self.handle_task_offload(task)

        # Return the response to the remote client
        header = net.createHeader(net.Commands.SCHEDULE_TASK)
        net.send(client_socket, header, response)


    # Method that schedules an edge node or a cloud node and then
    # sends the task to the scheduled node.
    def send_to_node(self, task, edge_timeout=5) -> bytes:
        # Attempt to make a connection to a node at most 3 times
        for _ in range(3):
            # Schedule either an edge or cloud node.
            scheduled_node: s.ScheduledNode = self.scheduler.schedule(
                task.deadline_ms / 1000,
                task.cycles_required,
                task.memory_requirement_mb
            )
            
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
                header = net.createHeader(net.Commands.SCHEDULE_TASK)
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
            self.diagnostics.addJob(task, scheduled_node, processing_time)

            self.diagnostics.incrementTasks()

            # Forward the raw response received from the remote node
            return response
        
        # Couldn't find an edge or cloud node in 3 attempts
        raise s.NoNodesExeception("Could not find an available edge or cloud node to schedule the task")
        
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

        added_node = self.scheduler.addNode((ip, port), registration.cpus, registration.clock_speed_cps, registration.memory_mb)
        if not added_node:
            return net.createResponse(False, b"Client already exists in the registry!")

        self.logger.info(f"Regstering node {ip}:{port} with {registration.cpus} cpus and {registration.memory_mb}mb memory")

        return net.createResponse(True, b"Success").SerializeToString()

    def handleRequest(self, sock, addr):
        parsed_header, raw_payload = net.recv(sock)
        response = b""

        match parsed_header.commandID:
            # Schedule task
            case net.Commands.SCHEDULE_TASK:
                incoming_request = (parsed_header, raw_payload)
                self.handle_task(incoming_request, sock)
                
                # Response will be sent in another method
                return

                # response = self.scheduleTask(parsed_header, raw_payload, self.diagnostics)
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
    logger = logging.getLogger(__name__)

    # cloud_ip = "LB1-6c7327e45f7a7b95.elb.eu-north-1.amazonaws.com"
    # cloud_ip = socket.gethostbyname(cloud_ip)
    # cloud_port = 8000
    # cloud_address = (cloud_ip, cloud_port)
    cloud_address = ("127.0.0.1", 16225)
    
    scheduler = s.SchedulerV1(
        logger=logger,
        cloud_address=cloud_address,
        cloud_clock_speed_cps=3.4*10**9, #3.4Ghz
        cloud_RTT_latency_s=0.7,
        load_factor_usage_threshold=1, 
        omega=0.01
    )
    
    diagnostics = Diagnostics(
        measurement_interval_s=20,
        scheduler=scheduler, 
        display=False
    )

    access_server = EdgeAccess(
        scheduler=scheduler,
        queue_wait_time_s=0.3,
        priority_task_threshold_s=0.45,
        logger= logger,
        diagnostics=diagnostics
    )

    access_server.serve()    

if __name__ == "__main__":
    main()








