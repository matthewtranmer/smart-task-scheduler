from dataclasses import dataclass

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
    REMOVE_BACKGROUND = 13

    # Parallel TaskIDs
    BANANA_QUALITY_RATING = 103
    ORANGE_QUALITY_RATING = 104

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
    TaskIDs.REMOVE_BACKGROUND: TaskParameters(cycles=229200000, memory_mb=100),
}

