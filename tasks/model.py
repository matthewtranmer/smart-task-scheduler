# pip install docker
import docker, socket, sys, io, json, time, re
from datetime import datetime, timezone
from docker.types import Resources, LogConfig

#0.311976250798 - addition
#0.618341801748 - multiplication
#1.47385531736 - division

IMAGE = "addition"

# Connect to the local docker daemon
client = docker.from_env()
lc = LogConfig(type=LogConfig.types.NONE)
lc = LogConfig(type=LogConfig.types.NONE)

def runtime_and_exit_from_events(cont):
    # Reads past events for this container; works even after auto-remove
    start_ns = end_ns = None
    exit_code = None
    for ev in cont.client.events(decode=True, since=0, filters={"container": cont.id}):
        act = ev.get("Action")
        if act == "start" and start_ns is None:
            start_ns = ev["timeNano"]
        elif act == "die":
            end_ns = ev["timeNano"]
            attrs = (ev.get("Actor") or {}).get("Attributes") or {}
            if "exitCode" in attrs:
                exit_code = int(attrs["exitCode"])
            break
    if start_ns is None or end_ns is None:
        raise RuntimeError("Missing start/die events")
    return (end_ns - start_ns), exit_code  # ns, int

def sendInput(client, container, data: bytes):
    sock = client.api.attach_socket(container.id, params={"stdin": 1, "stream": 1})
    try:
        sock._sock.sendall(data)
        sock._sock.shutdown(socket.SHUT_WR)
    finally:
        try: sock.close()
        except Exception: pass

def getOutput_no_wait(client, container):
    stdout_chunks, stderr_chunks = [], []
    # live stream; ends when the container exits
    for out, err in client.api.attach(container.id, stdout=True, stderr=True,
                                      stream=True, demux=True, logs=False):
        if out: stdout_chunks.append(out)
        if err: stderr_chunks.append(err)
    stdout = b"".join(stdout_chunks).decode("utf-8", "replace")
    stderr = b"".join(stderr_chunks).decode("utf-8", "replace")
    return stdout, stderr

def main():
    run_times = []
    for i in range(500):
        container = client.containers.create(
            IMAGE,
            stdin_open=True, tty=False, auto_remove=True,
            network_disabled=True,
            mem_limit="256m",
            cpu_quota=100_000,
            cpuset_cpus="2",
            read_only=True,
            log_config=lc,
            cap_add=["SYS_NICE"]
        )
        try:
            payload = json.dumps({"a": 2, "b": 20}).encode()

            # Start, feed stdin, capture output (no wait())
            container.start()
            sendInput(client, container, payload)
            stdout, stderr = getOutput_no_wait(client, container)

            # Precise runtime + exit code from events
            runtime_ns, exit_code = runtime_and_exit_from_events(container)
            runtime_s = runtime_ns / 1_000_000_000

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
    print("MAX:", max(run_times))
    print("MIN:", min(run_times))
    print("RANGE:", max(run_times) - min(run_times))

if __name__ == "__main__":
    main()