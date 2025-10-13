# pip install docker
import docker, socket, sys, io, json, time, re
from datetime import datetime, timezone
from docker.types import Resources, LogConfig
from lib import container



IMAGE = "addition"

# Connect to the local docker daemon
client = docker.from_env()
lc = LogConfig(type=LogConfig.types.NONE)
lc = LogConfig(type=LogConfig.types.NONE)




#0.311976250798 - UB - 0.47164257 - addition
#0.618341801748 - multiplication
#1.47385531736 - division

def main():
    run_times = []
    for i in range(500):
        
        try:
            payload = json.dumps({"a": 2, "b": 20}).encode()

            cont = container.Container(IMAGE)
            
            cont.sendInput(payload)
            stdout, stderr, exit_code = cont.getOutput()

            # Precise runtime + exit code from events
            runtime_ns = cont.runtime()
            runtime_s = runtime_ns / 1_000_000_000
            
            if (exit_code != 0):
                print("EXIT CODE:", exit_code)
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
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