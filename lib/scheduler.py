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

class Scheduler:
    index = 0
    nodes = []

    def schedule(self):
        raise NotImplementedError

    # Returns true if node is added to the registry, false if the node
    # already exists in the registry
    def addNode(self, address, cpus, memory_mb) -> bool:
        node = {
            "address": address,
            "cpus": cpus,
            "memory": memory_mb,
            "cpus_available": cpus,
            "memory_available": memory_mb,
            "timed_out": False
        }

        try:
            self._findNodeIndex(address)
            #Node must already exist
            return False
        
        except KeyError:
            self.nodes.append(node)
            return True

    def _findNodeIndex(self, address):
        node_index = 0
        for node in self.nodes:
            if node["address"] == address:
                return node_index
            
            node_index += 1

        raise KeyError
    
    def nodeHeartbeat(self, address):
        index = self._findNodeIndex(address)
        self.nodes[index]["timed_out"] = False

    def removeNode(self, address):
        node_index = self._findNodeIndex(address)
        print(f"removing node at index {node_index} --------------------------------------------------------")
        self.nodes.pop(node_index) 

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

class RoundRobin(Scheduler):
    def schedule(self) -> tuple[str, int]:
        if len(self.nodes) <= 0:
            return None

        if self.index >= len(self.nodes):
            self.index = 0

        scheduled_node = self.nodes[self.index]["address"]
        self.index += 1

        return scheduled_node
    
class RoundRobinWithAllocation(Scheduler):
    def schedule(self, memory_mb):
        if (len(self.nodes) <= 0):
            raise NoNodesExeception("There are no nodes available to perform the task")

        start_index = self.index

        foundNodeWithCPU = False
        foundNodeWithMemory = False
        while True:
            scheduled_node = None

            if self.nodes[self.index]["cpus_available"] > 0:
                foundNodeWithCPU = True

            if self.nodes[self.index]["memory_available"] > memory_mb:
                foundNodeWithMemory = True

            if self.nodes[self.index]["cpus_available"] > 0 and self.nodes[self.index]["memory_available"] > memory_mb:
                scheduled_node = self.nodes[self.index]

                scheduled_node["cpus_available"] -= 1
                scheduled_node["memory_available"] -= memory_mb
            
            self.index += 1
            if (self.index >= len(self.nodes)):
                self.index = 0

            if scheduled_node != None:
                return scheduled_node["address"]

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


    def resetNode(self, address, memory_mb):
        node_index = self._findNodeIndex(address)

        self.nodes[node_index]["cpus_available"] += 1
        self.nodes[node_index]["memory_available"] += memory_mb
        




















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