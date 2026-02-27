import random, socket
from lib import edge_pb2, task_definitions
from collections import deque

class DAGNode():
    node_id: int
    task_id: int
    completed: bool = False

    def __init__(self, task_id):
        self.task_id = task_id
        self.node_id = random.randint(1, 999999999999999999999999999999)

# TODO: Make threadsafe
# Need to have client socket to respond
class TaskDependencyGraph():
    task_id: int
    nodes: list[DAGNode] = []
    dependency_list: dict[int, list[int]] = {0: []}
    completed_nodes = 0
    
    result_storage: dict[int, bytes] = {}

    client_socket: socket.socket

    def __init__(self, client_socket: socket.socket, deadline_s: float):
        self.client_socket = client_socket
        self.deadline_s = deadline_s

    # Returns the subtasks deadline in seconds
    def calc_subtask_deadline(self, subtask_cycles: int) -> float:
        return subtask_cycles/self.total_subtask_cycles * self.deadline_s

    def add_node(self, node: DAGNode):
        self.nodes.append(node)

        return node.node_id
    
    def get_node(self, node_id: int) -> DAGNode:
        # Start Node ID
        if node_id == 0:
            return 0
        
        # End Node ID
        if node_id == -1:
            return -1
        
        for node in self.nodes:
            if node.node_id == node_id:
                return node
            
        return None

    # node_ids 0 and -1 are reserved for the start and end nodes
    def add_link(self, target_node_id: int, dependent_node_id: int):
        # Validate IDs
        if self.get_node(dependent_node_id) == None: raise ValueError("Node ID does not exist")
        if self.get_node(target_node_id) == None: raise ValueError("Node ID does not exist")

        # Add IDs to dependency list
        if target_node_id not in self.dependency_list:
            self.dependency_list[target_node_id] = [dependent_node_id, ]

        else:
            self.dependency_list[target_node_id].append(dependent_node_id)

    # Layered topological sorting using Kahn’s algorithm
    # based on iterative in-degree elimination
    def get_DAG_layers(self):    
        # Calculate number of edges coming into each node
        in_degree = {}
        for u in self.dependency_list:
            for v in self.dependency_list[u]:
                if v not in in_degree:
                    in_degree[v] = 0

                in_degree[v] += 1

            if u not in in_degree:
                if u not in in_degree:
                    in_degree[u] = 0

                in_degree[u] = in_degree[u]

        # Find inital nodes
        inital_nodes = []
        for n in in_degree:
            if in_degree[n] == 0:
                inital_nodes.append(n)

        # Create queue with inital nodes
        queue = deque(inital_nodes)
        
        # Build up layers
        layers = []
        while queue:
            current_layer = list(queue)
            layers.append(current_layer)
            
            next_queue = deque()
            
            while queue:
                node = queue.popleft()
                for neighbor in self.dependency_list.get(node, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            
            queue = next_queue

        return layers

    def get_dependencies(self, node_id: int):
        if node_id in self.dependency_list:
            return self.dependency_list[node_id]
        
        return []
    
    def calculate_layer_deadlines(self):
        layers = self.get_DAG_layers()
        # Pop first and last layer (start and stop layers)
        layers.pop()
        layers.pop(0)

        # Reverse layers so that the first layer is layer 1
        # This is due to the fact the graph is stored as a depedency list
        layers.reverse()

        max_cycles_per_layer: list[int] = []
        total_cycles_per_layer = 0

        for layer in layers:
            max_cycles = 0

            for node in layer:
                cycles = task_definitions.task_parameters[node.task_id].cycles

                if cycles > max_cycles:
                    max_cycles = cycles

            total_cycles_per_layer += max_cycles
            max_cycles_per_layer.append(max_cycles)

        self.layer_deadlines: list[float] = []
        for max_cycles in max_cycles_per_layer:
            deadline = max_cycles / total_cycles_per_layer * self.deadline_s
            self.layer_deadlines.append(deadline)

    #  Return a manifest of the start tasks
    def get_start_tasks(self) -> list[edge_pb2.Task]:
        self.calculate_layer_deadlines()

        start_task_nodes: list[DAGNode] = []

        # Get start tasks
        for key in self.dependency_list:
            if self.dependency_list[key] == [0, ]:
                start_task_nodes.append(key)

        tasks = []
        for node in start_task_nodes:
            params = task_definitions.task_parameters[node.task_id]

            task = edge_pb2.Task()
            task.inputID = random.randint(1000000000, 2147483640)
            task.taskID = node.task_id
            task.cycles_required = params.cycles
            task.memory_requirement_mb = params.memory_mb
            task.deadline_ms = self.layer_deadlines[0]

            tasks.append(task)

        return tasks

    # Called when a subtask has finished executing
    # Returns a list of tasks that can now be executed with their data populated
    # Returns True when the DAG task is complete
    def update_state(self, completed_node_id: int, result: bytes) -> list[edge_pb2.Task, bool]:
        self.result_storage[completed_node_id] = result
        self.get_node(completed_node_id).completed = True
        self.completed_nodes += 1

        if self.completed_nodes >= len(self.nodes):
            return [], True

        # Find nodes that were dependent on this task
        dependent_nodes = []

        for key in self.dependency_list:
            if completed_node_id in self.dependency_list[key]:
                dependent_nodes.append(key)

        print(f"dependent_nodes: {dependent_nodes}")

        executable_nodes: list[DAGNode] = []

        # Test if dependent nodes now have waiting dependecies
        for node_id in dependent_nodes:
            can_execute = True

            if node_id not in self.dependency_list:
                continue

            next_dependencies = self.dependency_list[node_id]
            for next_dependency_id in next_dependencies:
                if not self.get_node(next_dependency_id).completed:
                    can_execute = False
                    break

            if can_execute:
                executable_nodes.append(self.get_node(node_id))

        tasks = []
        for node in executable_nodes:
            params = task_definitions.task_parameters[node.task_id]

            task = edge_pb2.Task()
            task.inputID = random.randint(1000000000, 2147483640)
            task.taskID = node.task_id
            task.cycles_required = params.cycles
            task.memory_requirement_mb = params.memory_mb
            task.deadline_ms = self.layer_deadlines[0]

            tasks.append(task)

        return tasks, False
