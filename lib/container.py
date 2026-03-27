import sys
import docker, socket, random, os, json
from docker.types import LogConfig
import threading
import time, asyncio
from lib import edge_pb2, net

class NoContainersExeception(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class InternalContainerError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"


class Container:
    client = docker.from_env()

    def __init__(self, image, cpuset_cpus=None, timeout=10):
        self.container = self.client.containers.create(
            image,
            auto_remove=True,
            detach=True,
            cpuset_cpus=cpuset_cpus,
            ports={"8000/tcp": ("127.0.0.1", None)} # Chose a random port
        )

        self.containerID = self.container.id
        self.image = image
        self.cpuset_cpus = cpuset_cpus
        self.timeout = timeout
        self.sock = None

        self.container.start()
        self.container.reload()

        # Get the random port the container has chosen
        self.port = int(
            self.container.attrs["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"]
        )

        print(f"Container port: {self.port}")

    def getContainer(self):
        return self.container
    
    def setMemoryLimit(self, memory_bytes: int):
        self.client.api.update_container(
            self.containerID,
            mem_limit=memory_bytes,
            memswap_limit=memory_bytes
        )

    def executeTask(self, task: edge_pb2.Task) -> edge_pb2.ContainerResponse:
        # Convert task into a JSON string to give to the container
        # container_params = {"id": task.taskID, "params": task.input.decode(), "inputID": task.inputID}
        # json_params = json.dumps(container_params)

        # Start execution time counter
        start_time = time.perf_counter()
        # Send task to container
        self.send(task.SerializeToString())

        response = edge_pb2.ContainerResponse()
        inputID = -2147483648

        # Continue until we receive the indended output 
        while inputID != task.inputID:
            output = self.receive()

            response.ParseFromString(output)
            inputID = response.inputID

        # Calculate execution time
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        response.processing_time_ms = int(execution_time_ms)

        return response
    
    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", self.port))

        print("created socket")

    def send(self, data: bytes):
        if self.sock == None:
            self.create_socket()

        length_header = len(data).to_bytes(4, "big", signed=False)

        self.sock.sendall(length_header + data)

    # Returns the data in bytes, and True on an unhandled error
    def receive(self) -> bytes:
        if self.sock == None:
            self.create_socket()
            
        BUF_SIZE = 65536
        
        payload = self.sock.recv(BUF_SIZE)

        if payload == b'':
            raise EOFError("Connection closed by peer")

        if len(payload) < 4:
            raise ValueError("Header could not be read")
        
        length_bytes = payload[:4]        
        received_data = payload[4:]

        buffer_length = int.from_bytes(length_bytes, byteorder="big", signed=False)

        while len(received_data) < buffer_length:
            payload = self.sock.recv(BUF_SIZE)
            received_data += payload

        
        return received_data
    
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
        self.id = container.containerID

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.pool.releaseContainer(self)
    
class ContainerPool:
    containers: list[Container] = []
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

        for container in self.containers:
            container.create_socket()

    def getContainer(self, memory):
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
            print("Creating new container")
        else:
            # Get container from pool
            new_container = self.containers.pop(0) 

        self.lock.release()

        return PoolContainer(self, new_container, short_lived, memory)
    
    def releaseContainer(self, pool_container: PoolContainer):
        container_id = pool_container.container.containerID
        
        restart_container = False
        try:
            container = pool_container.container.client.containers.get(container_id)
            if container.status != "running":
                restart_container = True

        except docker.errors.NotFound:
            restart_container = True            

        # One off container
        if (pool_container.short_lived and restart_container):
            return
        
        if (pool_container.short_lived):
            print("Short lived, killing")
            pool_container.container.kill()
            return
        
        container = pool_container.container
        
        # If container has stopped, restart it
        if restart_container:
            container = Container(
                image=pool_container.container.image,
                cpuset_cpus=pool_container.container.cpuset_cpus
            )

            print("Restarted container")

        self.lock.acquire()
        self.containers.append(container)
        self.assigned_containers -= 1
        self.lock.release()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        print("Cleaning up containers")

        for cont in self.containers:
            cont.kill()

class StaticContainerPool(ContainerPool):
    def __init__(self, image, cpu_ids):
        self.image = image

        for id in cpu_ids:
            new_container = Container(image=image, cpuset_cpus=str(id))
            self.containers.append(new_container)

        for container in self.containers:
            container.create_socket()

    def getContainer(self):
        self.assigned_containers += 1

        if (len(self.containers) > 0):
            # Get container from pool
            new_container = self.containers.pop(0)
    
            return PoolContainer(self, new_container, short_lived=False)
            
        raise NoContainersExeception("All available containers are in use")
        
    def releaseContainer(self, pool_container):
        super().releaseContainer(pool_container)            