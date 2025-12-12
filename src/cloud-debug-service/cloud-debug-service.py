import sys, logging, socket, time, json, threading
from lib import net, edge_pb2
from lib.scheduler import Tasks

def handleRequest(remote, addr):
    print("Accepted connection")

    parsed_header, raw_payload = net.recv(remote)
    if (parsed_header.commandID != net.Commands.SCHEDULE_TASK):
        print("Error")
        
        remote.close()
        return

    task = edge_pb2.Task()
    task.ParseFromString(raw_payload)

    # Simulate network delay
    time.sleep(0.4)

    # Simulate task execution
    match task.inputID:
        case Tasks.DETECT_HUMAN:
            time.sleep(0.188)
        case Tasks.CLASSIFY_FRUIT:
            time.sleep(0.095)
        case Tasks.FRUIT_QUALITY:
            time.sleep(0.04)
        case Tasks.COMPRESSION:
            time.sleep(0.03)
        case Tasks.ENCRYPTION:
            time.sleep(0.03)

    response_text = {"value": "EXECUTED ON CLOUD", "inputID": task.inputID}
    response = net.createResponse(True, json.dumps(response_text).encode()).SerializeToString()
    net.send(remote, net.createHeader(parsed_header.commandID), response)
    
    print("Done")

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