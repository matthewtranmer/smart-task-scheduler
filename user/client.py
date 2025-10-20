import socket, time, threading, json, random, os
from lib import edge_pb2, net

access_server_address = ("10.45.1.34", 2004)

def createTask(taskID: int, input: bytes, deadline_ms: int):
    task = edge_pb2.Task()
    task.taskID = 0
    task.input = input
    task.deadline_ms = deadline_ms

    return task

def submitTask(task):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(access_server_address)

    header = net.createHeader(net.Commands.SCHEDULE_TASK)
    net.send(sock, header, task.SerializeToString())

    _, payload = net.recv(sock)

    sock.close()

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    return response

threads = []

def main():
    while True:
        a = random.randint(1,10)
        b = random.randint(1,10)

        payload = json.dumps({"a": a, "b": b}).encode()
        task = createTask(0, payload, 1000)

        print()
        print("Submitted Task")

        true_result = a + b

        print(f"true_result: {true_result}")
        print("a:", a)
        print("b:", b)

        start_time = time.time()
        response = submitTask(task)
        end_time = time.time()

        time_elapsed = end_time - start_time

        if(time_elapsed * 1000 > task.deadline_ms):
            print("DEADLINE MISSED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        print(f"Response: {response}")
        print(f"Elapsed time: {time_elapsed:.3f} seconds")

        res = response.value.decode()
        result = int(res.split()[0])
        
        print("Result from server:", result)

        if (result != true_result):
            print("Broken")
            os._exit(-1)
            

if __name__ == "__main__":
    for i in range(22):
        thread = threading.Thread(target=main).start()