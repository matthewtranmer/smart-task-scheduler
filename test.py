import json

from lib import container

cpu_time_ms = 2000
deadline_ms = 2000

json_data = json.dumps({"a":20, "b":1})

cont = container.Container("addition", cpu_time_ms*1000, cpu_time_ms*1000)
cont.sendInput(json_data.encode())
print(cont.getOutput())