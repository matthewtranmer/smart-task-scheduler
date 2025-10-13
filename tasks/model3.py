import json
from lib import container

cont = container.Container("task_sandbox")

for i in range(10000):
    data = json.dumps({"task_name": "addition", "a":1, "b":2})
    cont.send(data.encode())

    print(cont.receieveOutput())