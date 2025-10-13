import docker, socket
from docker.types import LogConfig
import asyncio
import time

class Container:
    client = docker.from_env()

    def __init__(self, image, pool_id=0):
        self.pool_id = pool_id

        self.container = self.client.containers.create(
            image,
            tty=False,
            stdin_open=True,
            auto_remove=True,
            network_disabled=True,
            cap_add=["SYS_NICE"],
            user="root", # Danger
            detach=True,
            read_only=True,              
        )

        self.container.start()

        self.sock = self.container.attach_socket(params={"stdin": 1, "stdout": 1, "stream": 1})
        self.sock._sock.settimeout(2)

    def getContainer(self):
        return self.container

    def send(self, data: bytes):
        self.sock._sock.sendall(data + b"\n")

    def _parseDockerHeader(self, header) -> dict:
        parsed_header = {}

        if (header[0] == 1):
            parsed_header["stream"] = "stdout" 
        elif (header[0] == 2):
            parsed_header["stream"] = "stderr"

        payload_length_bytes = header[4:]
        parsed_header["payload_length"] = int.from_bytes(payload_length_bytes, 'big', signed=False)

        return parsed_header

    def _recv(self) -> bytes:
        header = self.sock._sock.recv(8)
        parsed_header = self._parseDockerHeader(header)

        data = self.sock._sock.recv(parsed_header["payload_length"])
        return data

    def receieveOutput(self) -> str:
        return self._recv().decode().strip()
    
    def stop(self):
        self.container.stop()
    
    def getPoolID(self):
        return self.pool_id
    
class ContainerPool:
    containers = []
    max_container_count = 0
    current_container = 0
    assigned_containers = 0
    image = ""
    lock = asyncio.Lock()

    def __init__(self, image, container_count, max_container_count):
        self.max_container_count = max_container_count
        self.image = image

        for i in range(container_count):
            new_container = Container(image=image)
            self.containers.append(new_container)

    def getContainer(self):
        self.lock.acquire()

        if (self.assigned_containers <= self.max_container_count):
            self.assigned_containers += 1

        if (len(self.containers) <= 0):
            if (self.assigned_containers >= self.max_container_count):
                #Create short lived container (pool_id = 1)
                new_container = Container(self.image, 1)
            else:
                #Create new container
                new_container = Container(self.image)
        else:
            # Get container from pool
            new_container = self.containers.pop(0) 

        self.lock.release()
        return new_container
    
    def releaseContainer(self, container: Container):
        # One off container
        if (container.getPoolID() == 1):
            container.stop()
            return

        self.lock.acquire()
        self.containers.append(container)
        self.lock.release()
