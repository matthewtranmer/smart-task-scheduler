import random, json, base64, math
from lib import edge_pb2, task_definitions
from collections import deque

# A node within the DAG graph
class DAGNode():
    node_id: int
    task_id: int
    task: edge_pb2.Task
    completed: bool = False

    def __init__(self, task_id):
        self.task_id = task_id

        params = task_definitions.task_parameters[task_id]

        self.task = edge_pb2.Task()
        self.task.inputID = random.randint(1000000000, 2147483640)
        self.task.taskID = task_id
        self.task.cycles_required = params.cycles
        self.task.memory_requirement_mb = params.memory_mb
        self.task.deadline_ms = 0

        self.node_id = random.randint(1, 999999999999999999999999999999)

# Graph definition for DAG tasks
class TaskDependencyGraph():
    START_NODE_ID = 0
    END_NODE_ID = -1
    
    def __init__(self, deadline_s: float):
        self.deadline_s = deadline_s
        self.deadline_ms = deadline_s * 1000

        self.task_id: int
        self.nodes: list[DAGNode] = []
        
        self.dependency_list: dict[int, list[int]] = {0: []}
        self.result_storage: dict[int, bytes] = {}
        
        self.completed_nodes = 0
        self.task_canceled = False

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

    def get_dependencies(self, node_id: int):
        if node_id in self.dependency_list:
            return self.dependency_list[node_id]
        
        return []
    
    def get_neighbours(self, node_id: int) -> list[int]:
        neighbours = []

        # Find all the nodes that have a dependency on node_id
        for node in self.dependency_list:
            if node_id in self.dependency_list[node]:
                neighbours.append(node)

        return neighbours

    # Get the paths in the graph using DFS
    def get_paths(self):
        start_nodes = []
        end_nodes = self.dependency_list[self.END_NODE_ID]

        # Find start nodes
        for node in self.dependency_list:
            dependencies = self.dependency_list[node]

            if self.START_NODE_ID in dependencies and len(dependencies) == 1:
                start_nodes.append(node)

        paths = []

        for start in start_nodes:
            stack = [(start, [start])]

            while len(stack) > 0:
                node, path = stack.pop()

                if node in end_nodes:
                    paths.append(path)
                    continue

                # Add neighbors to stack
                for neighbor in self.get_neighbours(node):
                    stack.append((neighbor, path + [neighbor]))

        return paths

    def calculate_task_deadlines(self):
        paths = self.get_paths()

        for path in paths:
            path_weight = 0

            # Calculate the path weight (total cycles required for the path)
            for node_id in path:
                node = self.get_node(node_id)
                path_weight += node.task.cycles_required
            
            # print(f"Path: {path}, weight: {path_weight}")

            # Assign deadlines
            for node_id in path:
                node = self.get_node(node_id)

                node_deadline_ms = math.ceil((float(node.task.cycles_required) / float(path_weight)) * self.deadline_ms)
                if node_deadline_ms < node.task.deadline_ms or node.task.deadline_ms == 0:
                    node.task.deadline_ms = node_deadline_ms

        # for node in self.nodes:
            # print(f"Assigned deadline {node.task.deadline_ms}ms to taskID {node.task.taskID}")

    #  Return a manifest of the start tasks and the node ids
    def get_start_tasks(self, input_data: bytes) -> tuple[list[edge_pb2.Task], list[int]]:
        self.calculate_task_deadlines()

        start_task_nodes: list[DAGNode] = []

        # Get start tasks
        for key in self.dependency_list:
            if self.dependency_list[key] == [0, ]:
                start_task_nodes.append(self.get_node(key))

        tasks = []
        nodes = []
        for node in start_task_nodes:
            node.task.input = input_data

            tasks.append(node.task)
            nodes.append(node.node_id)

        return tasks, nodes
    
    def cancel_task(self):
        self.task_canceled = True

    # Called when a subtask has finished executing
    # Returns a list of tasks that can now be executed with their data populated
    # Returns their node IDs within the graph
    # Returns True when the DAG task is complete
    # Sets self.final_result when completed
    def update_state(self, completed_node_id: int, result: bytes) -> tuple[list[edge_pb2.Task], list[int], bool]:
        if self.task_canceled:
            return [], [], False

        # Store task result
        self.result_storage[completed_node_id] = result

        self.get_node(completed_node_id).completed = True
        self.completed_nodes += 1

        # If all nodes have completed - return
        if self.completed_nodes >= len(self.nodes):
            self.final_result = result
            return [], [], True

        # Find nodes that were dependent on this task
        dependent_nodes = []

        for key in self.dependency_list:
            if completed_node_id in self.dependency_list[key]:
                dependent_nodes.append(key)

        # print(f"dependent_nodes: {dependent_nodes}")

        executable_nodes: list[DAGNode] = []

        # Find nodes that can now execute
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

        # Create task manifests with the correct inputs from the storage
        tasks = []
        nodes = []
        for node in executable_nodes:
            # Get inputs from dependent nodes - labeled by task id
            input_list = {}
            dependent_nodes = self.dependency_list[node.node_id]

            for dependent_node_id in dependent_nodes:
                dependent_task_id = self.get_node(dependent_node_id).task_id

                # print(f"New input detected: {self.result_storage[dependent_node_id][:40]}")

                # Encode outputs from tasks as base 64 strings encodeable by JSON
                data_b64_str = base64.encodebytes(self.result_storage[dependent_node_id]).decode()
                input_list[dependent_task_id] = data_b64_str

            node.task.input = json.dumps(input_list).encode()

            nodes.append(node.node_id)
            tasks.append(node.task)

        return tasks, nodes, False
