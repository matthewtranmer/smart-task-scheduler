import socket, json, base64
from lib import edge_pb2, net
from lib.scheduler import Tasks 

def decode_binary(binary_in: str) -> bytes:
    return base64.decodebytes(binary_in.encode())

def encode_binary(binary_in: bytes) -> str:
    return base64.encodebytes(binary_in).decode()

class TaskOffloader:
    def __init__(self, access_server_addr):
        self.access_server_addr = access_server_addr

    def detectHuman(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.DETECT_HUMAN
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def classifyFruit(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.CLASSIFY_FRUIT
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def fruitQuality(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.FRUIT_QUALITY
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)

    # Compresses data - input raw data in bytes
    # - returns compressed data in bytes
    def compress(self, data: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.COMPRESSION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    # Decompresses data - input compressed data in bytes
    # - returns decompressed data as base64 string
    def decompress(self, data: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.DECOMPRESSION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def encrypt(self, key: bytes, plaintext: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.ENCRYPTION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def decrypt(self, key: bytes, ciphertext: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.ENCRYPTION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def fruit_size(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.FRUIT_SIZE
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def fruit_defects(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.FRUIT_DEFECTS
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def object_count(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.OBJECT_COUNT
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)

    # Fake tasks ************

    def addition(self, key: bytes, a: int, b: int, deadline_ms: int) -> edge_pb2.Response:
        params = {"a": a, "b": b}
        json_params = json.dumps(params)
        
        task = edge_pb2.Task()
        task.taskID = Tasks.ADDITION
        task.input = json_params.encode()
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def multiplication(self, key: bytes, a: int, b: int, deadline_ms: int) -> edge_pb2.Response:
        params = {"a": a, "b": b}
        json_params = json.dumps(params)
        
        task = edge_pb2.Task()
        task.taskID = Tasks.MULTIPLICATION
        task.input = json_params.encode()
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def division(self, key: bytes, a: int, b: int, deadline_ms: int) -> edge_pb2.Response:
        params = {"a": a, "b": b}
        json_params = json.dumps(params)
        
        task = edge_pb2.Task()
        task.taskID = Tasks.DIVISION
        task.input = json_params.encode()
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    # TESTING -------------------------------------

    def _test_orange_ripeness(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.ORANGE_QUALITY_RIPENESS
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)

    def _test_banana_ripeness(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = Tasks.BANANA_QUALITY_RIPENESS
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)


    def _submitTask(self, task) -> edge_pb2.Response:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.access_server_addr)

        header = net.createHeader(net.Commands.SCHEDULE_TASK)

        serialised_task = task.SerializeToString()
        net.send(sock, header, serialised_task)

        _, payload = net.recv(sock)

        sock.close()

        response = edge_pb2.Response()
        response.ParseFromString(payload)

        return response