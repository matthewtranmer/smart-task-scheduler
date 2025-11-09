import socket, time, threading, random, json, os, sys, logging
from lib import edge_pb2, net, container, system
from lib.taskHandler import CloudClient

def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
  
    logger = logging.getLogger(__name__)

    edge_client = CloudClient(
        logger=logger,
        port=16225
    )

    edge_client.serve("task_sandbox", timeout=5)

if __name__ == "__main__":
    main()