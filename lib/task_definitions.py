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
    TaskIDs.DETECT_HUMAN: TaskParameters(cycles=624843909, memory_mb=68),
    TaskIDs.CLASSIFY_FRUIT: TaskParameters(cycles=296498930, memory_mb=66),
    TaskIDs.FRUIT_QUALITY: TaskParameters(cycles=131351691, memory_mb=61),
    TaskIDs.COMPRESSION: TaskParameters(cycles=5173250, memory_mb=38),
    TaskIDs.DECOMPRESSION: TaskParameters(cycles=2697808, memory_mb=38),
    TaskIDs.ENCRYPTION: TaskParameters(cycles=6842475, memory_mb=41),
    TaskIDs.DECRYPTION: TaskParameters(cycles=8199410, memory_mb=42),
    TaskIDs.BANANA_QUALITY_RIPENESS: TaskParameters(cycles=458188233, memory_mb=110),
    TaskIDs.ORANGE_QUALITY_RIPENESS: TaskParameters(cycles=459502736, memory_mb=111),
    TaskIDs.FRUIT_SIZE: TaskParameters(cycles=181905621, memory_mb=53),
    TaskIDs.FRUIT_DEFECTS: TaskParameters(cycles=136_565_240, memory_mb=64),
    TaskIDs.FRUIT_QUALITY_AGGREGATION: TaskParameters(cycles=10_000_000, memory_mb=38),
    TaskIDs.OBJECT_COUNT: TaskParameters(cycles=80207002, memory_mb=47),
    TaskIDs.REMOVE_BACKGROUND: TaskParameters(cycles=2000568258, memory_mb=316),
}

