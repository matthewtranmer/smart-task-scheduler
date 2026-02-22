from multiprocessing import Lock

class NoNodesExeception(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"
    
class NodeResourceExecpetion(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"
    
class Tasks():
    DETECT_HUMAN = 0
    CLASSIFY_FRUIT = 1
    FRUIT_QUALITY = 2
    COMPRESSION = 3
    DECOMPRESSION = 4
    ENCRYPTION = 5
    DECRYPTION = 6
    ADDITION = 100
    MULTIPLICATION = 101
    DIVISION = 102

    @staticmethod
    def getName(task_id):
        names = {
            Tasks.DETECT_HUMAN: "Detect Human",
            Tasks.CLASSIFY_FRUIT: "Classify Fruit",
            Tasks.FRUIT_QUALITY: "Fruit Quality",
            Tasks.COMPRESSION: "Compression",
            Tasks.ENCRYPTION: "Encryption",
            Tasks.ADDITION: "Addition",
            Tasks.MULTIPLICATION: "Multiplication",
            Tasks.DIVISION: "Division",
        }
        return names.get(task_id, f"Unknown({task_id})")

class NodeType:
    EDGE = 0
    CLOUD = 1

class ScheduledNode:
    def __init__(self, address: tuple[str, int], node_type: int, memory_mb=None):
        self.address = address
        self.node_type = node_type
        self.memory_mb = memory_mb

class Scheduler:
    index = 0
    nodes = []
    next_id = 0

    def schedule(self) -> ScheduledNode:
        raise NotImplementedError
    
    def calculateResourceUsage(self, sample_time_s) -> list:
        for node in self.nodes:
            cpu_time_per_second = node["cpu_time_ms"] // sample_time_s
            available_processing_time = node["cpus"] * 1000

            cpu_usage_percent = min(cpu_time_per_second / available_processing_time * 100, 100)
            cpu_usage_percent = round(cpu_usage_percent, 2)

            node["cpu_time_ms"] = 0
            node["cpu_usage"] = cpu_usage_percent

    def resetNode(self, scheduledNode: ScheduledNode, processing_time_ms) -> bool:
        if scheduledNode.node_type == NodeType.CLOUD:
            return True

        try:
            node_index = self._findNodeIndex(scheduledNode.address)
        except KeyError:
            return False

        self.nodes[node_index]["cpus_available"] += 1
        self.nodes[node_index]["memory_available"] += scheduledNode.memory_mb
        self.nodes[node_index]["cpu_time_ms"] += processing_time_ms
        self.nodes[node_index]["assigned_tasks"] -= 1

        return True

    # Returns true if node is added to the registry, false if the node
    # already exists in the registry
    def addNode(self, address, cpus, memory_mb) -> bool:
        node = {
            "address": address,
            "cpus": cpus,
            "memory": memory_mb,
            "cpus_available": cpus,
            "memory_available": memory_mb,
            "timed_out": False,
            "id":self.next_id,
            "cpu_time_ms": 0,
            "cpu_usage": 0,
            "assigned_tasks": 0
        }

        try:
            self._findNodeIndex(address)
            #Node must already exist
            return False
        except KeyError:
            self.nodes.append(node)
            self.next_id += 1

            return True

    def _findNodeIndex(self, address):
        node_index = 0
        
        for node in self.nodes:
            if node["address"] == address:
                return node_index
            
            node_index += 1

        raise KeyError("The node does not exist")
    
    def nodeHeartbeat(self, address):
        index = self._findNodeIndex(address)
        self.nodes[index]["timed_out"] = False

    def removeNode(self, scheduled_node: ScheduledNode) -> bool:
        if (scheduled_node.node_type == NodeType.CLOUD):
            return
        
        try:
            node_index = self._findNodeIndex(scheduled_node.address)
        except KeyError:
            return False
        
        print(f"removing node at index {node_index} --------------------------------------------------------")
        self.nodes.pop(node_index) 

        return True

    # Returns addresses of dead nodes
    def removeDeadNodes(self) -> list[tuple[str, int]]:
        nodes_removed = []
        
        index = 0
        for node in self.nodes:
            if (node["timed_out"] == True):
                nodes_removed.append(node)
                self.nodes.pop(index)
            else:
                node["timed_out"] = True

            index += 1

        return nodes_removed
    
    def getNodes(self):
        return self.nodes
    
    def getNodeID(self, address):
        index = self._findNodeIndex(address)
        return self.nodes[index]["id"]

# class RoundRobin(Scheduler):
#     def schedule(self) -> tuple[str, int]:
#         if len(self.nodes) <= 0:
#             return None

#         if self.index >= len(self.nodes):
#             self.index = 0

#         scheduled_node = self.nodes[self.index]["address"]
#         self.index += 1

#         return scheduled_node


    
class RoundRobinWithAllocation(Scheduler):
    def schedule(self, memory_mb) -> ScheduledNode:
        if (len(self.nodes) <= 0):
            raise NoNodesExeception("There are no nodes available to perform the task")

        if (self.index >= len(self.nodes)):
            self.index = 0
        start_index = self.index
        
        foundNodeWithCPU = False
        foundNodeWithMemory = False
        while True:
            scheduled_node = None

            # try:
            # Found a node with enough CPU
            if self.nodes[self.index]["cpus_available"] > 0:
                foundNodeWithCPU = True

            # Found a node with enough memory
            if self.nodes[self.index]["memory_available"] > memory_mb:
                foundNodeWithMemory = True

            # Node has both enough cpu and memory to schedule task
            if self.nodes[self.index]["cpus_available"] > 0 and self.nodes[self.index]["memory_available"] > memory_mb:
                scheduled_node = self.nodes[self.index]

                scheduled_node["cpus_available"] -= 1
                scheduled_node["memory_available"] -= memory_mb
                scheduled_node["assigned_tasks"] += 1
            # except IndexError:
            #     raise NoNodesExeception("There are no nodes available to perform the task")

            self.index += 1
            if (self.index >= len(self.nodes)):
                self.index = 0

            # Found a suitable node
            if scheduled_node != None:
                return ScheduledNode(scheduled_node["address"], NodeType.EDGE, memory_mb=memory_mb)

            # Wrap around - checked all nodes
            if self.index == start_index:
                # Couldnt find a node with either enough cpu and memory
                if not foundNodeWithCPU and not foundNodeWithMemory:
                    raise NodeResourceExecpetion("There are no nodes with enough resources available")
                # Found a node with enough memory - but not enough CPU
                elif foundNodeWithMemory:
                    raise NodeResourceExecpetion("There are no nodes with enough CPU available")
                # Found a node with enough CPU - but not enough memory
                else:
                    raise NodeResourceExecpetion("There are no nodes with enough memory available")

class RoundRobinEdgeCloud(RoundRobinWithAllocation):
    def __init__(self, cloud_address):
        self.cloud_address = cloud_address

    def schedule(self, memory_mb):
        try:
            return super().schedule(memory_mb)
        except (NoNodesExeception, NodeResourceExecpetion) as e:
            return ScheduledNode(self.cloud_address, NodeType.CLOUD, memory_mb)
        
    def resetNode(self, scheduledNode, processing_time_ms):
        if (scheduledNode.node_type == NodeType.EDGE):
            super().resetNode(scheduledNode, processing_time_ms)


#TODO:  CPUs available is becoming -1?????????????????/

# TODO: not thread safe
class SchedulerV1(Scheduler):
    lock = Lock()

    # High omega - score nodes with more free memory higher
    # Low omega - score nodes with more free CPUs higher
    def __init__(self, cloud_address, omega=0.8):
        self.cloud_address = cloud_address
        self.omega = omega

    def schedule(self, task_memory_mb) -> ScheduledNode:
        # pprint.pprint(self.nodes)

        with self.lock:
            best_node = None
            top_score = 0

            print("scores: ", end="")
            # Find the node with the best score
            for node in self.nodes:
                node_score = self._score_node(node, task_memory_mb)

                print(f"score:{node_score}, ", end="")

                if (node_score > top_score):
                    top_score = node_score
                    best_node = node

            # No edge nodes available to process task
            if (top_score == 0):
                print("GOT SCORE OF 0 - SENDING TO CLOUD")
                return ScheduledNode(self.cloud_address, NodeType.CLOUD, task_memory_mb)

            print("DIDN'T GET SCORE OF ZEROR - SENDING TO EDGE")
            print(f"Best node had {best_node["cpus_available"]} CPUs available before scheduling")
            print(f"Best node had {best_node["memory_available"]}mb available before scheduling")

            best_node["cpus_available"] -= 1
            best_node["memory_available"] -= task_memory_mb
            best_node["assigned_tasks"] += 1

            print(f"Best node now has {best_node["cpus_available"]} CPUs available after scheduling")
            print(f"NEW memory availible: {best_node["memory_available"]}")

            if (best_node["cpus_available"] < 0):
                print("GONE NEGATIVE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")

            # Schedule to edge node with highest score
            return ScheduledNode(best_node["address"], NodeType.EDGE, task_memory_mb)

    def _score_node(self, node, task_memory_mb) -> int:
        memory_available: int = node["memory_available"]
        cpus_available: int = node["cpus_available"]

        print(f"_score_node(): cpus available = {cpus_available}")

        memory_total: int = node["memory"]
        cpus_total: int = node["cpus"]

        # Return score of 0 if there isn't enough memory on the node to perform the task
        if (memory_available < task_memory_mb):
            return 0
        
        # Return a score of 0 if there isn't a free CPU on the node to perform the task
        if (cpus_available < 1):
            return 0
        
        # Calculate resource used if task were to be scheduled
        new_memory_usage: int = (memory_available - task_memory_mb) / memory_total   
        new_CPU_usage: int = (cpus_available - 1) / cpus_total

        # Score the node
        score: int = (self.omega * new_memory_usage) +  (1 - self.omega) * new_CPU_usage
        return score
        
        
        



# class Scheduler:
#     # current_node = 0

#     # # Returns the index of the next node to be scheduled in the edge clients list.
#     # # Returns -1 if there are no available nodes
#     # def schedule(self, edge_clients): 
#     #     if len(edge_clients) == 0:
#     #         return -1

#     #     if self.current_node >= len(edge_clients):
#     #         self.current_node = 0
        
#     #     node_index = self.current_node
#     #     self.current_node += 1

#     #     return node_index