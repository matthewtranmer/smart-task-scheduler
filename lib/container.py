import docker, socket
from docker.types import LogConfig

class Container:
    client = docker.from_env()
    lc = LogConfig(type=LogConfig.types.NONE)

    def __init__(self, image, cpu_time_ms=None, deadline_ms=None):
        cpu_time_us = ""
        deadline_us = ""

        if (cpu_time_ms != None and deadline_ms != None):
            cpu_time_us = cpu_time_ms * 1000
            deadline_us = deadline_ms * 1000

        self.container = self.client.containers.create(
            image,
            stdin_open=True,
            tty=False,
            auto_remove=True,
            network_disabled=True,
            cap_add=["SYS_NICE"],
            user="root",
            detach=False,
            read_only=True,              
            tmpfs={
                "/tmp": "rw,size=64m",   # RAM-backed scratch dirs
                "/run": "rw,size=16m",
                "/var/log": "rw,size=16m"
            },
            log_config=self.lc
        )

        self.container.start()

    def getContainer(self):
        return self.container

    def sendInput(self, data):
        # Attach a socket to the containers standard I/O streams 
        sock = self.client.api.attach_socket(self.container.id, params={"stdin":1, "stream":1})

        # Stream input data to stdin
        sock._sock.sendall(data)
        # Close stdin
        sock._sock.shutdown(socket.SHUT_WR) 

    def getOutput(self):
        # Read output as it arrives
        stdout_chunks = []
        stderr_chunks = []

        # Connect to the container
        stream = self.client.api.attach(self.container.id, stdout=True, stderr=True, stream=True, demux=True)
        for out in stream:
            if out[0]:
                stdout_chunks.append(out[0])
            if out[1]:
                stderr_chunks.append(out[1])

        # Wait for exit & get status code
        status = self.container.wait()  # {'StatusCode': int}
        status_code = status.get("StatusCode", -1)

        # Convert to string
        stdout = b"".join(stdout_chunks)
        stderr = b"".join(stderr_chunks)

        return (stdout, stderr, status_code)
    
    # Return execution time in ns
    def runtime(self):
        # Reads past events for this container; works even after auto-remove
        start_ns = end_ns = None

        for ev in self.container.client.events(decode=True, since=0, filters={"container": self.container.id}):
            act = ev.get("Action")
            if act == "start" and start_ns is None:
                start_ns = ev["timeNano"]
            
            elif act == "die":
                end_ns = ev["timeNano"]
                break

        if start_ns is None or end_ns is None:
            raise RuntimeError("Missing start/die events")
        return end_ns - start_ns
    
class ContainerPool:
    containers = []

    def __init__(self, image, container_count):
        for i in range(container_count):
            new_container = Container(image=image)

    def getContainer(self):
        pass