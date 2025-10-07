class Scheduler():
    current_node = 0

    # Returns the index of the next node to be scheduled in the edge clients list.
    # Returns -1 if there are no available nodes
    def schedule(self, edge_clients): 
        if len(edge_clients) == 0:
            return -1

        if self.current_node >= len(edge_clients):
            self.current_node = 0
        
        node_index = self.current_node
        self.current_node += 1

        return node_index