import json
from lib.task_definitions import TaskIDs

def fruit_quality_aggregation(json_data: bytes) -> bytes:
    data_dict = json.loads(json_data.decode())

    RIPENESS_WEIGHT = 0.5
    SIZE_WEIGHT = 0.2
    DEFECTS_WEIGHT = 0.3
 
    if str(TaskIDs.BANANA_QUALITY_RIPENESS) in data_dict:
        ripeness_str = data_dict[str(TaskIDs.BANANA_QUALITY_RIPENESS)]
    elif str(TaskIDs.ORANGE_QUALITY_RIPENESS) in data_dict:
        ripeness_str = data_dict[str(TaskIDs.ORANGE_QUALITY_RIPENESS)]

    # raise Exception(f"ripeness_str: {ripeness_str}")

    match ripeness_str:
        case "rotten":
            ripeness = 0
        case "unripe":
            ripeness = 0.5
        case "fresh":
            ripeness = 1
    
    size = float(data_dict[str(TaskIDs.FRUIT_SIZE)])
    defects = float(data_dict[str(TaskIDs.FRUIT_DEFECTS)]) 

    # Test result - simply add together
    # TODO: implement properly
    result = ripeness + size + defects
    return str(result).encode()
