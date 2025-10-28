import socket, json, pprint, os
from flask import Flask, render_template
from lib import net, edge_pb2

app = Flask(__name__)
access_server_address = ("10.45.1.34", 2004)

@app.route("/")
def hello_world():
    data = gatherDiagnostics()
    return render_template("index.html", data=data)

def gatherDiagnostics() -> dict:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(access_server_address)

    header = net.createHeader(net.Commands.GATHER_DIAGNOSTICS)
    net.send(sock, header, b"")

    _, payload = net.recv(sock)

    sock.close()

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    diagnostics = json.loads(response.value)
    return diagnostics

# diagnostics = gatherDiagnostics()
# pprint.pprint(diagnostics)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
