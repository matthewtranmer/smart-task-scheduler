import json, base64
from lib.task_definitions import TaskIDs

def fruit_quality_aggregation(json_data: bytes) -> bytes:
    data_dict = json.loads(json_data.decode())

    RIPENESS_WEIGHT = 0.5
    SIZE_WEIGHT = 0.2
    DEFECTS_WEIGHT = 0.3
 
    if str(TaskIDs.BANANA_QUALITY_RIPENESS) in data_dict:
        ripeness_data = data_dict[str(TaskIDs.BANANA_QUALITY_RIPENESS)]
    elif str(TaskIDs.ORANGE_QUALITY_RIPENESS) in data_dict:
        ripeness_data = data_dict[str(TaskIDs.ORANGE_QUALITY_RIPENESS)]

    ripeness_str = base64.decodebytes(ripeness_data.encode()).decode()

    match ripeness_str:
        case "rotten":
            ripeness = 0
        case "unripe":
            ripeness = 0.5
        case "fresh":
            ripeness = 1
        case _:
            raise Exception("Ripeness given in incorrect format")
    
    size = float(base64.decodebytes(data_dict[str(TaskIDs.FRUIT_SIZE)].encode()).decode())
    defects = float(base64.decodebytes(data_dict[str(TaskIDs.FRUIT_DEFECTS)].encode()).decode())

    # Test result - simply add together
    # TODO: implement properly
    test = f"ripeness: {ripeness}, size: {size}, defects: {defects}"
    return str(test).encode()
