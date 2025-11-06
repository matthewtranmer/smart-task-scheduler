import socket, time, threading, json, random, os, traceback, sys, base64
from lib import edge_pb2, net

class TaskOffloader:
    def __init__(self, access_server_addr):
        self.access_server_addr = access_server_addr

    def detectHuman(self, image_bytes, deadline) -> edge_pb2.Response:
        payload = json.dumps({"img_bytes": base64.encodebytes(image_bytes).decode()}).encode()

        task = net.createTask(
            taskID=net.Tasks.DETECT_HUMAN,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def classifyFruit(self, image_bytes, deadline) -> edge_pb2.Response:
        payload = json.dumps({"img_bytes": image_bytes}).encode()

        task = net.createTask(
            taskID=net.Tasks.CLASSIFY_FRUIT,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def fruitQuality(self, image_bytes, deadline) -> edge_pb2.Response:
        payload = json.dumps({"img_bytes": image_bytes}).encode()

        task = net.createTask(
            taskID=net.Tasks.FRUIT_QUALITY,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def compress(self, data, deadline) -> edge_pb2.Response:
        payload = json.dumps({"data": data}).encode()

        task = net.createTask(
            taskID=net.Tasks.COMPRESSION,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def encrypt(self, key, plaintext, deadline) -> edge_pb2.Response:
        payload = json.dumps({"key": key, "plaintext": plaintext}).encode()

        task = net.createTask(
            taskID=net.Tasks.ENCRYPTION,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def addition(self, a, b, deadline) -> edge_pb2.Response:
        payload = json.dumps({"a": a, "b": b}).encode()

        task = net.createTask(
            taskID=net.Tasks.ADDITION,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def multiplication(self, a, b, deadline) -> edge_pb2.Response:
        payload = json.dumps({"a": a, "b": b}).encode()

        task = net.createTask(
            taskID=net.Tasks.MULTIPLICATION,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def division(self, a, b, deadline) -> edge_pb2.Response:
        payload = json.dumps({"a": a, "b": b}).encode()

        task = net.createTask(
            taskID=net.Tasks.DIVISION,
            input=payload,
            memory_requirement_mb=300,
            deadline_ms=deadline,
            inputID=random.randint(10000,9999999)
        )

        return self._submitTask(task)

    def _submitTask(self, task) -> edge_pb2.Response:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.access_server_addr)

        header = net.createHeader(net.Commands.SCHEDULE_TASK)

        serialised_task = task.SerializeToString()
        print(f"Task length: {len(serialised_task)}")
        net.send(sock, header, serialised_task)

        _, payload = net.recv(sock)

        sock.close()

        response = edge_pb2.Response()
        response.ParseFromString(payload)

        return response

def main(address):
    try:
        offloader = TaskOffloader(address)

        with open("1.jpg", "rb") as f:
                image_bytes = f.read()

        while True:
            deadline = 1000
            a = random.randint(1, 99)
            b = random.randint(1, 99)

            start_time = time.perf_counter()
            # response = offloader.addition(a, b, deadline)
            
            response = offloader.detectHuman(image_bytes, deadline)

            end_time = time.perf_counter()

            time_elapsed = end_time - start_time

            print(f"Time Elapsed {time_elapsed}")
            print(f"Response {response}")

            

    except Exception as e:
        print("CLIENT SIDE EXECEPTION")
        traceback.print_exc()
        os._exit(-1)
        

if __name__ == "__main__":
    address = None
    threads = 1

    if len(sys.argv) > 1:
        threads = int(sys.argv[1])

    if len(sys.argv) > 2:
        address = sys.argv[2]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    for i in range(threads):
        thread = threading.Thread(target=main, args=(address, )).start()