from multiprocessing import Lock
import logging

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
    
class TaskDroppedExeception(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"
    
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
    
    # Calculates the mean clock speed between the edge nodes
    def calculate_average_clock_speed(self) -> int:
        total = 0
        count = 0

        for node in self.nodes:
            total += node["clock_speed"]
            count += 1

        return int(total / count)
    
    def calculate_processing_time(self, clock_speed, cycles_required):
        return cycles_required / clock_speed
    
    def calculate_cloud_processing_time(self, cycles_required):
        processing_time = self.calculate_processing_time(self.cloud_clock_speed_cps, cycles_required)
        
        return processing_time + self.cloud_RTT_latency_s
    
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
    def addNode(self, address, cpus, clock_speed, memory_mb) -> bool:
        node = {
            "address": address,
            "cpus": cpus,
            "clock_speed": clock_speed,
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
    def __init__(
            self, 
            logger: logging.Logger,
            cloud_address: tuple[str, int], # The address where cloud tasks are scheduled to
            cloud_clock_speed_cps: int, # Cloud clock speed in cycles per second
            cloud_RTT_latency_s: float, # The network delay when sending a task to the cloud 
            load_factor_usage_threshold: float, # Threshold when tasks are preemptively scheduled to the cloud 
            omega: float # Resource priority when calculating each node's score  
        ):
        self.logger: logging.Logger = logger
        self.cloud_address: tuple[str, int] = cloud_address
        self.cloud_clock_speed_cps: int = cloud_clock_speed_cps
        self.cloud_RTT_latency_s: float = cloud_RTT_latency_s
        self.load_factor_usage_threshold: float = load_factor_usage_threshold
        self.omega: float = omega

    def _get_best_node(self, task_deadline_s, task_cycles_required, task_memory_mb) -> tuple[dict, int]:
        best_node = None
        top_score = 0
        # count = 0

        # Find the node with the best score
        for node in self.nodes:
            node_score = self._score_node(
                node, 
                task_deadline_s, 
                task_cycles_required, 
                task_memory_mb
            )

            # self.logger.debug(f"Node {count} got score {node_score}")
            # self.logger.debug(f"Node {count} CPUs available {node["cpus_available"]}")
            

            # count += 1

            if (node_score > top_score):
                top_score = node_score
                best_node = node

        return (best_node, top_score)

    def schedule(self, task_deadline_s, task_cycles_required, task_memory_mb) -> ScheduledNode:
        with self.lock:

            load_factor = self._calculate_load_factor()
            print(f"load_factor: {load_factor}")
            if load_factor > self.load_factor_usage_threshold:
                self.logger.debug(f"Load factor above threshold")

                # Calculate if task can be sent to the cloud without exceeding deadline
                cloud_execution_time = self.calculate_cloud_processing_time(task_cycles_required)


                # print(f"cloud_execution_time: {cloud_execution_time}")
                # print(f"task_deadline_s: {task_deadline_s}")

                if cloud_execution_time < task_deadline_s:
                    self.logger.info("High load factor mitigation - sending long deadline task to cloud")
                    return ScheduledNode(self.cloud_address, NodeType.CLOUD, task_memory_mb)

            # Calculate best edge node using scoring system
            best_node, top_score = self._get_best_node(
                task_deadline_s,
                task_cycles_required,
                task_memory_mb
            )

            # print(top_score)

            # No edge nodes available to process task
            if (top_score == 0):
                print(f"Nodes detected {len(self.nodes)}")
                self.logger.info("No free edge nodes available to process task")

                # Test if task is viable to run on the cloud
                cloud_execution_time = self.calculate_cloud_processing_time(task_cycles_required)
                if cloud_execution_time < task_deadline_s:
                    return ScheduledNode(self.cloud_address, NodeType.CLOUD, task_memory_mb)

                # Task won't be able to be completed in time - drop
                self.logger.info("Task dropped!!")
                raise TaskDroppedExeception("Task will not be able to be executed before the given deadline!")

            best_node["cpus_available"] -= 1
            best_node["memory_available"] -= task_memory_mb
            best_node["assigned_tasks"] += 1

            if (best_node["cpus_available"] < 0):
                self.logger.error("CPUs available stat has gone negative")

            # Schedule to edge node with highest score
            return ScheduledNode(best_node["address"], NodeType.EDGE, task_memory_mb)

    def _score_node(self, node, task_deadline_s, task_cycles_required, task_memory_mb) -> int:
        memory_available: int = node["memory_available"]
        cpus_available: int = node["cpus_available"]

        memory_total: int = node["memory"]
        cpus_total: int = node["cpus"]

        # Return score of 0 if there isn't enough memory on the node to perform the task
        if (memory_available < task_memory_mb):
            self.logger.debug("Edge node doesn't have enough free memory to complete task")

            return 0
        
        # Return a score of 0 if there isn't a free CPU on the node to perform the task
        if (cpus_available < 1):
            self.logger.debug("Edge node doesn't have enough free CPUs to complete task")

            return 0
                
        # If task won't complete on edge node in time, return score of 0
        processing_time = self.calculate_processing_time(node["clock_speed"], task_cycles_required)
        # print(f"processing_time: {processing_time}")
        # print(f"node['clock_speed']: {node["clock_speed"]}")
        if (processing_time > task_deadline_s):
            self.logger.debug("Task won't execute on edge node before deadline")

            return 0
        
        # Calculate resource used if task were to be scheduled
        new_memory_usage: int = (memory_available - task_memory_mb) / memory_total   
        new_CPU_usage: int = (cpus_available - 1) / cpus_total

        # Score the node
        score: int = (self.omega * new_memory_usage) +  (1 - self.omega) * new_CPU_usage
        return score
    
    # The higher the load factor - the higher the resource usage 
    def _calculate_load_factor(self):
        cpus_used = 0
        cpus_total = 0
        
        for node in self.nodes:
            node_total_cpus = node["cpus"]
            node_used_cpus = node_total_cpus - node["cpus_available"] 

            cpus_used += node_used_cpus
            cpus_total += node_total_cpus

        # If there are no CPUs - same as if all CPUs are taken
        if cpus_total == 0:
            return 1

        return cpus_used / cpus_total
            
        