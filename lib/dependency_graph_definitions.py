from lib import dagtask as d
from lib.task_definitions import TaskIDs

class BananaQualityRating(d.TaskDependencyGraph):
    def __init__(self, deadline_s: float):
        super().__init__(deadline_s)

        self.task_id = TaskIDs.BANANA_QUALITY_RATING

        # Create Graph Nodes
        ripeness_id = self.add_node(d.DAGNode(TaskIDs.BANANA_QUALITY_RIPENESS))
        defects_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_DEFECTS))
        size_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_SIZE))
        quality_aggregation_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_QUALITY_AGGREGATION))

        self.ripeness_id = ripeness_id
        self.defects_id = defects_id
        self.size_id = size_id
        self.quality_grading_id = quality_aggregation_id

        # Create Graph Links
        self.add_link(ripeness_id, 0)
        self.add_link(defects_id, 0)
        self.add_link(size_id, 0)

        self.add_link(quality_aggregation_id, ripeness_id)
        self.add_link(quality_aggregation_id, defects_id)
        self.add_link(quality_aggregation_id, size_id)

        self.add_link(-1, quality_aggregation_id)

class OrangeQualityRating(d.TaskDependencyGraph):
    def __init__(self, deadline_s: float):
        super().__init__(deadline_s)

        self.task_id = TaskIDs.ORANGE_QUALITY_RATING

        # Create Graph Nodes
        ripeness_id = self.add_node(d.DAGNode(TaskIDs.ORANGE_QUALITY_RIPENESS))
        defects_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_DEFECTS))
        size_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_SIZE))
        quality_aggregation_id = self.add_node(d.DAGNode(TaskIDs.FRUIT_QUALITY_AGGREGATION))

        self.ripeness_id = ripeness_id
        self.defects_id = defects_id
        self.size_id = size_id
        self.quality_grading_id = quality_aggregation_id

        # Create Graph Links
        self.add_link(ripeness_id, 0)
        self.add_link(defects_id, 0)
        self.add_link(size_id, 0)

        self.add_link(quality_aggregation_id, ripeness_id)
        self.add_link(quality_aggregation_id, defects_id)
        self.add_link(quality_aggregation_id, size_id)

        self.add_link(-1, quality_aggregation_id)

parallel_task_IDs = [
    TaskIDs.BANANA_QUALITY_RATING,
    TaskIDs.ORANGE_QUALITY_RATING
]

# Maps task ID to dependency graph
dag_tasks: dict[int, d.TaskDependencyGraph] = {
    TaskIDs.BANANA_QUALITY_RATING : BananaQualityRating,
    TaskIDs.ORANGE_QUALITY_RATING: OrangeQualityRating,
}

def get_dag_task_implementation(task_id: int) -> d.TaskDependencyGraph:
    return dag_tasks[task_id]