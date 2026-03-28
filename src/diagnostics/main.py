import socket, json, pprint, os, sys
from flask import Flask, render_template
from lib import net, edge_pb2

app = Flask(__name__)

@app.route("/")
def index():
    print("Index")
    data = gatherDiagnostics()
    return render_template("index.html", data=data)

def gatherDiagnostics() -> dict:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(access_server_address)
    print("Connected")

    header = net.createHeader(net.Commands.GATHER_DIAGNOSTICS)
    net.send(sock, header, b"")
    print("Send")

    _, payload = net.recv(sock)
    print("recv")

    sock.close()

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    diagnostics = json.loads(response.value)
    return diagnostics

# diagnostics = gatherDiagnostics()
# pprint.pprint(diagnostics)


if __name__ == "__main__":
    address = None
    if len(sys.argv) > 1:
        address = sys.argv[1]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    if address != None:
        access_server_address = address

    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
