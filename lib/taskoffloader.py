import socket, json, base64
from lib import edge_pb2, net
from lib.task_definitions import TaskIDs

def decode_binary(binary_in: str) -> bytes:
    return base64.decodebytes(binary_in.encode())

def encode_binary(binary_in: bytes) -> str:
    return base64.encodebytes(binary_in).decode()

# Class that handles offloading user tasks to the access service
class TaskOffloader:
    def __init__(self, access_server_addr):
        self.access_server_addr = access_server_addr

    def detectHuman(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.DETECT_HUMAN
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def classifyFruit(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.CLASSIFY_FRUIT
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def fruitQuality(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.FRUIT_QUALITY
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)

    # Compresses data - input raw data in bytes
    # - returns compressed data in bytes
    def compress(self, data: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.COMPRESSION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    # Decompresses data - input compressed data in bytes
    # - returns decompressed data as base64 string
    def decompress(self, data: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.DECOMPRESSION
        task.input = data
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def encrypt(self, key: bytes, plaintext: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.ENCRYPTION
        task.input = json.dumps({
            "key": base64.encodebytes(key).decode(),
            "plaintext": plaintext.decode(), 
        }).encode()
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def decrypt(self, key: bytes, ciphertext: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.DECRYPTION
        task.input = json.dumps({
            "key": base64.encodebytes(key).decode(),
            "ciphertext": ciphertext.decode(), 
        }).encode()
        task.deadline_ms = deadline_ms

        return self._submitTask(task)

    
    def object_count(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.OBJECT_COUNT
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    # Parallel tasks ***********
    def banana_quality_rating(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.BANANA_QUALITY_RATING
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    
    def orange_quality_rating(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.ORANGE_QUALITY_RATING
        task.input = image_bytes
        task.deadline_ms = deadline_ms

        return self._submitTask(task)
    

    def REMOVE_BG_TEST(self, image_bytes: bytes, deadline_ms: int) -> edge_pb2.Response:
        task = edge_pb2.Task()
        task.taskID = TaskIDs.REMOVE_BACKGROUND
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