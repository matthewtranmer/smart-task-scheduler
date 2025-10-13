# pip install docker
import docker, socket, sys, io, json, time, re
from datetime import datetime, timezone
from docker.types import Resources, LogConfig
from lib import container



IMAGE = "task_sandbox"

# Connect to the local docker daemon
# Traceback (most recent call last):\n  File "/app/main.py", line 53, in <module>\n    main()\n    ~~~~^^\n  File "/app/main.py", line 42, in main\n    match input["task_name"]:\n          ~~~~~^^^^^^^^^^^^^\nKeyError: \'task_name\'\n'


#0.311976250798 - UB - 0.47164257 - addition
#0.618341801748 - multiplication
#1.47385531736 - division

def main():
    run_times = []

    payload = json.dumps({"task_name": "addition", "a": 2, "b": 30}).encode()
    cont = container.Container(IMAGE)

    for i in range(10):
        
        try:
            print(cont.getContainer().id)

            print(1)
            cont.sendInput(payload)
            print(2)
            stdout = cont.getOutput()
            print(3)

            # Precise runtime + exit code from events
            runtime_ns = cont.runtime()
            runtime_s = runtime_ns / 1_000_000_000

            print("STDOUT:", stdout)
            # print("STDERR:", stderr)
            print("Runtime:", runtime_s)


            run_times.append(runtime_s)

        finally:
            # Optional: nothing to remove; auto_remove=True
            pass


    print("Done")
    mean = sum(run_times)/len(run_times)
    print("MEAN:", mean)
    print("MAX - MEAN:", max(run_times) - mean)
    print("MAX:", max(run_times))
    print("MEAN - MIN:", mean - min(run_times))
    print("MIN:", min(run_times))
    print("RANGE:", max(run_times) - min(run_times))

if __name__ == "__main__":
    main()