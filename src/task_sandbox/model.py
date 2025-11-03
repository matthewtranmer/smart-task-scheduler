from lib import container
import json, time, math, statistics

input = {"inputID": 0, "params": {"a": 2, "b": 4}, "id": 0}
json_input = json.dumps(input)

times = []

with container.ContainerPool("task_sandbox", 1, 1000) as pool:
    time.sleep(3)

    for i in range(100):
        with pool.getContainer() as pool_container:
            start = time.perf_counter()
            pool_container.container.send(json_input.encode())
            data = pool_container.container.receive()
            end = time.perf_counter()

            time_elapsed = end - start
            times.append(time_elapsed)

            print(time_elapsed)

print(f"MEAN: {statistics.mean(times)}")
print(f"MAX: {max(times)}")
print(f"MIN: {min(times)}")
