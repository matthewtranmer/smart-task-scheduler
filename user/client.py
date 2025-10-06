import socket
from lib import edge_pb2, net


task = edge_pb2.Task()
task.taskID = 0
task.input = b"Hello"

data = task.SerializeToString()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 2004))

header = net.createHeader(1)
net.send(sock, header, data)
print("Done")

sock.close()

