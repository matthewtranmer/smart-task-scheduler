import sys, logging, socket, time, json
from lib import net, edge_pb2


def main(address):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    access_server_address = address    
    logger = logging.getLogger(__name__)

    # edge_client = CloudClient(
    #     logger=logger,
    #     access_server_address=access_server_address
    # )

    # edge_client.serve("task_sandbox", timeout=5)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("10.45.1.34", 16225))

    sock.listen()

    print("Starting server")
    while True:
        remote, addr = sock.accept()
        print("Accepted connection")
        # Simulate network delay
        time.sleep(0.5)

        parsed_header, raw_payload = net.recv(remote)
        if (parsed_header.commandID != net.Commands.SCHEDULE_TASK):
            print("Error")
            
            remote.close()
            continue

        task = edge_pb2.Task()
        task.ParseFromString(raw_payload)

        # Simulate task execution
        time.sleep(1.5)

        response_text = {"value": "EXECUTED ON CLOUD", "inputID": task.inputID}
        response = net.createResponse(True, json.dumps(response_text).encode()).SerializeToString()
        net.send(remote, net.createHeader(parsed_header.commandID), response)
        
        print("Done")

if __name__ == "__main__":
    address = None
    if len(sys.argv) > 1:
        address = sys.argv[1]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    main(address)