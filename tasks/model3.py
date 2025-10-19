import json, time
from lib import container

cont = container.Container("task_sandbox")

for i in range(1):
    data = json.dumps({"id": 0, "params": "\"{\"a\":1, \"b\":2}\""})
    cont.send(data.encode())
    time.sleep(1)
    print(cont.receive())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())
    # print(cont.receieveOutput())

# pool = container.ContainerPool("task_sandbox", 1, 10)  
# pool_container = pool.getContainer()

# for i in range(10):
#     data = json.dumps({"task_name": "addition", "a":1, "b":2})
#     pool_container.container.send(data.encode())

#     print(pool_container.container.receieveOutput())





# data = json.dumps({"task_name": "addition", "a":1, "b":2})

# with container.ContainerPool("task_sandbox", 1, 10) as pool:
#     print(len(pool.containers))
#     with pool.getContainer() as pool_container:
#         for i in range(10):
#             data = json.dumps(
#                 {
#                  "task_name": "addition", 
#                  "task_params": json.dumps({"a":1, "b":2})
#                  }
#                 )
#             pool_container.container.send(data.encode())

#             print(pool_container.container.receieveOutput())
#     print(len(pool.containers))
