from lib import dagtask as d
from lib.task_definitions import TaskIDs

class BananaQualityRating(d.TaskDependencyGraph):
    def __init__(self, deadline_s: float):
        super().__init__(deadline_s)

        self.task_id = TaskIDs.BANANA_QUALITY_RATING

        # Create Graph Nodes
        self.remove_bg_id = self.add_node(d.DAGNode(TaskIDs.REMOVE_BACKGROUND))
        self.ripeness_id = self.add_node(d.DAGNode(TaskIDs.BANANA_QUALITY_RIPENESS))
        self.defects_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_DEFECTS))
        self.size_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_SIZE))
        self.quality_aggregation_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_QUALITY_AGGREGATION))

        # Create Graph Links
        self.add_link(self.ripeness_id, 0)
        self.add_link(self.remove_bg_id, 0)

        self.add_link(self.defects_id, self.remove_bg_id)
        self.add_link(self.size_id, self.remove_bg_id)

        self.add_link(self.quality_aggregation_id, self.ripeness_id)
        self.add_link(self.quality_aggregation_id, self.defects_id)
        self.add_link(self.quality_aggregation_id, self.size_id)

        self.add_link(-1, self.quality_aggregation_id)

class OrangeQualityRating(d.TaskDependencyGraph):
    def __init__(self, deadline_s: float):
        super().__init__(deadline_s)

        self.task_id = TaskIDs.ORANGE_QUALITY_RATING

        # Create Graph Nodes
        self.remove_bg_id = self.add_node(d.DAGNode(TaskIDs.REMOVE_BACKGROUND))
        self.ripeness_id = self.add_node(d.DAGNode(TaskIDs.ORANGE_QUALITY_RIPENESS))
        self.defects_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_DEFECTS))
        self.size_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_SIZE))
        self.quality_aggregation_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_QUALITY_AGGREGATION))

        # Create Graph Links
        self.add_link(self.ripeness_id, 0)
        self.add_link(self.remove_bg_id, 0)

        self.add_link(self.defects_id, self.remove_bg_id)
        self.add_link(self.size_id, self.remove_bg_id)

        self.add_link(self.quality_aggregation_id, self.ripeness_id)
        self.add_link(self.quality_aggregation_id, self.defects_id)
        self.add_link(self.quality_aggregation_id, self.size_id)

        self.add_link(-1, self.quality_aggregation_id)

parallel_task_IDs = [
    TaskIDs.BANANA_QUALITY_RATING,
    TaskIDs.ORANGE_QUALITY_RATING
]

# Maps task ID to dependency graph
dag_tasks: dict[int, d.TaskDependencyGraph] = {
    TaskIDs.BANANA_QUALITY_RATING: BananaQualityRating,
    TaskIDs.ORANGE_QUALITY_RATING: OrangeQualityRating,
}

def get_dag_task_implementation(task_id: int) -> d.TaskDependencyGraph:
    return dag_tasks[task_id]