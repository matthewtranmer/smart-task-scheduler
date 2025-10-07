import socket
from lib import edge_pb2, net

while True:

    task = edge_pb2.Task()
    task.taskID = 0
    task.input = b"Hello"

    data = task.SerializeToString()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 2004))

    header = net.createHeader(net.Commands.SCHEDULE_TASK)
    net.send(sock, header, data)
    print("Done")

    response_header, payload = net.recv(sock)

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    print(response)

    sock.close()

