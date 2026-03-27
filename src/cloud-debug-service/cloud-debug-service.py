import sys, logging, socket, time, json, threading
from lib import net, edge_pb2
from lib.task_definitions import TaskIDs, task_parameters
# import numpy as np
# import io

RTT_DELAY_S = 0.7
CLOUD_CYCLES_CPS = 3_400_000_000

with open("src/cloud-debug-service/orange_removed_bg.png", "rb") as file:
    image_bytes = file.read() 

# np_arr = np.frombuffer(image_bytes, np.uint8)
# buffer = io.BytesIO()
# np_arr.save(buffer, format='PNG')
# orange_removed_bg = buffer.getvalue()


def handleRequest(remote, addr):
    parsed_header, raw_payload = net.recv(remote)
    if (parsed_header.commandID != net.Commands.SCHEDULE_TASK):
        print("Error - SCHEDULE_TASK only implemented")
        
        remote.close()
        return

    task = edge_pb2.Task()
    task.ParseFromString(raw_payload)

    taskID = task.taskID

    print(f"executing taskID {taskID} on cloud")

    # Simulate network delay
    time.sleep(RTT_DELAY_S)

    result = ""
    cycles = 0

    if taskID not in task_parameters:
        print("TASK ID NOT FOUND!")
        cycles = 3_000_000_00
    else:
        cycles = task_parameters[taskID].cycles

    match taskID:
        case TaskIDs.DETECT_HUMAN:
            result = b"true"
        case TaskIDs.CLASSIFY_FRUIT:
            result = b"banana"
        case TaskIDs.COMPRESSION:
            result = b'\x1f\x8b\x08\x00. \xc4i\x02\xff\xed\xc71\r\x00 \x0c\x000qd7"\x18\x1f\x81\x87%\xc8\xc7H\xfb5\xde\x1cug\xf6\xdd\xd6\xa9\x0cUUUUUUUUUUUUUU\xad\xfc\xfd]w\xd1L\x1d\x00\x00'
        case TaskIDs.DECOMPRESSION:
            result = b"ExecutedOnCloud"*500
        case TaskIDs.ENCRYPTION:
            result = b'LQ/D+mKeBwXVntQFYXEAbCbusdSiiScwhpSDzDLjTn0Mqw9+7kqDtbEHRA=='
        case TaskIDs.DECRYPTION:
            result = b"ExecutedOnCloud"
        
        case TaskIDs.BANANA_QUALITY_RIPENESS:
            result = b"fresh"
        case TaskIDs.ORANGE_QUALITY_RIPENESS:
            result = b"fresh"

        case TaskIDs.FRUIT_DEFECTS:
            result = b"1"
        case TaskIDs.FRUIT_SIZE:
            result = b"1"
        
        case TaskIDs.OBJECT_COUNT:
            result = b"1"

        case TaskIDs.FRUIT_QUALITY_AGGREGATION:
            result = b"1"

        case TaskIDs.REMOVE_BACKGROUND:
            result = image_bytes

    delay = cycles / CLOUD_CYCLES_CPS
    time.sleep(delay)

    response = net.createResponse(True, result).SerializeToString()
    net.send(remote, net.createHeader(parsed_header.commandID), response)
    
    print(f"completed taskID {taskID}")

def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 16225))

    sock.listen()

    print(f"Server started on {sock.getsockname()}")

    while True:
        remote, addr = sock.accept()

        threading.Thread(target=handleRequest, args=(remote, addr)).start()

if __name__ == "__main__":
    main()