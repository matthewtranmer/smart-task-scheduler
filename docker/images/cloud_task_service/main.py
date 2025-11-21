import socket, threading, json, os, logging, traceback
from lib import edge_pb2, net
from src import task as task_helper
import queue

class CloudClient:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    task_queue = queue.Queue()

    def __init__(
            self,
            logger: logging.Logger, 
            ip="0.0.0.0", 
            port=8000
        ):
        self.logger = logger

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))
        self.ip, self.port = self.server.getsockname()
        self.server.listen()

        logger.info(f"Cloud client started on address {self.ip}:{self.port}")

    def serve(self, timeout=5):
        self.timeout = timeout

        # Start consumer thread
        thread = threading.Thread(target=self.handleRequest)
        thread.start()

        try:
            while True:
                sock, addr = self.server.accept()
                sock.settimeout(timeout)

                self.task_queue.put(sock)

                if (not thread.is_alive):
                    break

        except Exception as e:
            logging.ERROR(f"Exception raised in serve function {e}")
            os._exit(-1)

    def scheduleTask(self, payload):
        task = edge_pb2.Task()
        task.ParseFromString(payload)

        self.logger.info(f"Executing task with id {task.taskID}")

        params = json.loads(task.input.decode())
        result = task_helper.run_task(task.taskID, params)

        response = {"value": result, "inputID": task.inputID}
        return net.createResponse(True, json.dumps(response).encode())

    def handleRequest(self):
        while True:
            try:
                sock = self.task_queue.get()

                queue_size = self.task_queue.qsize()
                if (queue_size > 4):
                    self.logger.warning(f"Queue size is {queue_size}!!")

                parsed_header, raw_payload = net.recv(sock)   

                response = b""
                if (parsed_header.commandID == net.Commands.SCHEDULE_TASK):
                    response = self.scheduleTask(raw_payload)

                else:
                    response = net.createResponse(False, b"Command does not exist")

                header = net.createHeader(parsed_header.commandID)
                net.send(sock, header, response.SerializeToString())
            except:
                traceback.print_exc()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        #filename='edge-access-log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
  
    logger = logging.getLogger(__name__)
    
    client = CloudClient(logger=logger)
    client.serve()