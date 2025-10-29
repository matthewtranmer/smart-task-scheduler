import socket, time, threading, json, random, os, traceback, sys
from lib import edge_pb2, net

access_server_address = ("10.45.1.34", 2004)

def submitTask(task) -> edge_pb2.Response:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(access_server_address)

    header = net.createHeader(net.Commands.SCHEDULE_TASK)
    net.send(sock, header, task.SerializeToString())

    _, payload = net.recv(sock)

    sock.close()

    response = edge_pb2.Response()
    response.ParseFromString(payload)

    return response

threads = []

def main():
    try:
        while True:
            a = random.randint(1,50)
            b = random.randint(1,50)

            payload = json.dumps({"a": a, "b": b}).encode()

            input_id = random.randint(10000,9999999)

            task = net.createTask(
                taskID=0,
                input=payload,
                memory_requirement_mb=300,
                deadline_ms=1000,
                inputID=input_id
            )

            print()
            print("Submitted Task --------------------------------")

            true_result = a + b

            print(f"true_result: {true_result}")
            print("a:", a)
            print("b:", b)

            start_time = time.perf_counter()
            response = submitTask(task)
            end_time = time.perf_counter()

            time_elapsed = end_time - start_time

            if(time_elapsed * 1000 > task.deadline_ms):
                print("DEADLINE MISSED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            print(f"Received task {input_id} Response: {response}")
            print(f"Elapsed time: {time_elapsed:.3f} seconds")

            json_response = response.value.decode()
            try:
                parsed_response = json.loads(json_response)
            except Exception as e:
                print(e)

            if (response.success == False):
                print(json_response)
                time.sleep(0.3)
                continue

            result = int(parsed_response["value"])
            
            print("Result from server:", result)

            if (input_id != parsed_response["inputID"]):
                print("Dont match")

            if (result != true_result):
                print("Broken")

            if (input_id != parsed_response["inputID"] or result != true_result):
                os._exit(-1)

    except Exception as e:
        print("CLIENT SIDE EXECEPTION")
        traceback.print_exc()
        os._exit(-1)
        

if __name__ == "__main__":
    address = None
    threads = 1

    if len(sys.argv) > 1:
        threads = int(sys.argv[1])

    if len(sys.argv) > 2:
        address = sys.argv[2]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    if address != None:
        access_server_address = address

    for i in range(threads):
        thread = threading.Thread(target=main).start()