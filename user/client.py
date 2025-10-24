import socket, time, threading, json, random, os, traceback
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
            task = net.createTask(0, payload, 1000, input_id)

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
                for _ in range(100):
                    print(json_response)
                    
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
    for i in range(10):
        thread = threading.Thread(target=main).start()