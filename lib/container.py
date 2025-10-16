import docker, socket
from docker.types import LogConfig
import threading
import time

class Container:
    client = docker.from_env()

    def __init__(self, image):
        self.container = self.client.containers.create(
            image,
            tty=False,
            stdin_open=True,
            auto_remove=True,
            network_disabled=True,
            cap_add=["SYS_NICE"],
            user="root", # Danger - change in prod
            detach=True,
            read_only=True,              
        )

        self.container.start()

        self.sock = self.container.attach_socket(params={"stdin": 1, "stdout": 1, "stderr": 1,"stream": 1})
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
        if (len(header) < 8):
            return b''
        
        parsed_header = self._parseDockerHeader(header)

        data = self.sock._sock.recv(parsed_header["payload_length"])
        return data

    def receieveOutput(self) -> str:
        return self._recv().decode().strip()
    
    def stop(self):
        self.container.stop()

    def kill(self):
        self.container.kill()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()

class PoolContainer():
    pool = None
    container = None
    short_lived = False

    def __init__(self, pool, container, short_lived=False):
        self.pool = pool
        self.container = container
        self.short_lived = short_lived

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.pool.releaseContainer(self)
    
class ContainerPool:
    containers = []
    max_container_count = 0
    current_container = 0
    assigned_containers = 0
    image = ""
    lock = threading.Lock()

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

        short_lived = False
        if (len(self.containers) <= 0):
            if (self.assigned_containers > self.max_container_count):
                #Create short lived container
                print("Making short lived container") 
                short_lived = True

            #Create new container
            new_container = Container(self.image)
        else:
            # Get container from pool
            new_container = self.containers.pop(0) 

        self.lock.release()
        return PoolContainer(self, new_container, short_lived)
    
    def releaseContainer(self, pool_container: PoolContainer):
        # One off container
        if (pool_container.short_lived == True):
            print("Short lived, killing")
            pool_container.container.kill()
            return

        self.lock.acquire()
        self.containers.append(pool_container.container)
        self.lock.release()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        print("Cleaning up containers")
        for cont in self.containers:
            cont.kill()
