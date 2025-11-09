import socket, time, threading, random, json, os, sys, logging
from lib import edge_pb2, net, container, system
from lib.taskHandler import EdgeClient

def main(address):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    access_server_address = address    
    logger = logging.getLogger(__name__)

    edge_client = EdgeClient(
        logger=logger,
        access_server_address=access_server_address
    )

    edge_client.serve("task_sandbox", timeout=5)

if __name__ == "__main__":
    address = None
    if len(sys.argv) > 1:
        address = sys.argv[1]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    main(address)