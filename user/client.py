import socket, time, threading, json
from lib import edge_pb2, net

def createTask(taskID: int, input: bytes, deadline_ms: int):
    task = edge_pb2.Task()
    task.taskID = 0
    task.input = input
    task.deadline_ms = deadline_ms

    return task

def submitTask(task):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 2004))

    header = net.createHeader(net.Commands.SCHEDULE_TASK)
    net.send(sock, header, task.SerializeToString())

    _, payload = net.recv(sock)

    sock.close()

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    return response

def main():
    while True:
        payload = json.dumps({"a": 2, "b": 20}).encode()
        task = createTask(0, payload, 1000)

        print("Submitted Task")

        start_time = time.time()
        response = submitTask(task)
        end_time = time.time()

        time_elapsed = end_time - start_time

        if(time_elapsed * 1000 > task.deadline_ms):
            print("DEADLINE MISSED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        print(f"Response: {response}")
        print(f"Elapsed time: {time_elapsed:.3f} seconds")

if __name__ == "__main__":
    for i in range(15):
        threading.Thread(target=main).start()

# Things needed now:
# Diagnostics
# Implement a task
# Improve scheduler so we schedule based on free resources
# Thread safety - have a long think about this



# Task - Double exponentiation:
# a^b^c % 999,999,999
# where a < 99, a < 21 and c < 5