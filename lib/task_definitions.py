from dataclasses import dataclass
from lib import dagtask as d

@dataclass
class TaskParameters:
    cycles: int
    memory_mb: int

class TaskIDs():
    # Normal TaskIDs
    DETECT_HUMAN = 0
    CLASSIFY_FRUIT = 1
    FRUIT_QUALITY = 2
    COMPRESSION = 3
    DECOMPRESSION = 4
    ENCRYPTION = 5
    DECRYPTION = 6
    BANANA_QUALITY_RIPENESS = 7
    ORANGE_QUALITY_RIPENESS = 8
    FRUIT_SIZE = 9
    FRUIT_DEFECTS = 10
    FRUIT_QUALITY_AGGREGATION = 11
    OBJECT_COUNT = 12

    # Parallel TaskIDs
    BANANA_QUALITY_RATING = 13
    ORANGE_QUALITY_RATING = 14

    # Test TaskIDs
    ADDITION = 10001
    MULTIPLICATION = 10002
    DIVISION = 10003

task_parameters: dict[int, TaskParameters] = {
    TaskIDs.DETECT_HUMAN: TaskParameters(cycles=632400000, memory_mb=100),
    TaskIDs.CLASSIFY_FRUIT: TaskParameters(cycles=309400000, memory_mb=300),
    TaskIDs.FRUIT_QUALITY: TaskParameters(cycles=129200000, memory_mb=600),
    TaskIDs.COMPRESSION: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.DECOMPRESSION: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.ENCRYPTION: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.DECRYPTION: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.BANANA_QUALITY_RIPENESS: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.ORANGE_QUALITY_RIPENESS: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.FRUIT_SIZE: TaskParameters(cycles=929200000, memory_mb=100),
    TaskIDs.FRUIT_DEFECTS: TaskParameters(cycles=929200000, memory_mb=100),
    TaskIDs.FRUIT_QUALITY_AGGREGATION: TaskParameters(cycles=129200000, memory_mb=100),
    TaskIDs.OBJECT_COUNT: TaskParameters(cycles=129200000, memory_mb=100),
}

class BananaQualityRating(d.TaskDependancyGraph):
    def __init__(self):
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

class OrangeQualityRating(d.TaskDependancyGraph):
    def __init__(self):
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
dag_tasks: dict[int, d.TaskDependancyGraph] = {
    TaskIDs.BANANA_QUALITY_RATING : BananaQualityRating,
    TaskIDs.ORANGE_QUALITY_RATING: OrangeQualityRating,
}