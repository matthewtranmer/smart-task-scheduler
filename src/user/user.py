import socket, time, threading, json, random, os, traceback, sys, base64
from lib import edge_pb2, net, taskoffloader
from lib.scheduler import Tasks 

def main(address):
    try:
        offloader = taskoffloader.TaskOffloader(address)

        with open("src/user/test_data/human.jpg", "rb") as f:
                image_bytes = f.read()

        while True:
            deadline = 1000
            
            start_time = time.perf_counter()

            task_id = random.randint(0, 2)
            # task_id = 7
            match task_id:
                case 0:
                        print("DETECT HUMAN")
                        response = offloader.detectHuman(image_bytes, deadline)
                case 1:
                        print("CLASSIFY FRUIT")
                        response = offloader.classifyFruit(image_bytes, deadline)
                case 2:
                        print("FRUIT QUALITY")
                        response = offloader.fruitQuality(image_bytes, deadline)
                case 3:
                        print("COMPRESSION")
                        data = "This is some data that needs to be compressed. " * 20
                        response = offloader.compress(data, deadline)
                case 4:
                        print("DECOMPRESSION")
                        data = "This is some data that needs to be compressed. " * 20
                        response = offloader.decompress(data, deadline)
                case 5:
                        print("ENCRYPTION")
                        response = offloader.encrypt("keykeykeykeykey1", "This is some plaintext data to be encrypted.", deadline)
                case 6:
                        print("DECRYPTION")
                        response = offloader.decrypt("keykeykeykeykey1", "U2FsdGVkX1+I3V6Y5G6u1g6X9s6jZ0bX5Zl5r8QvV3I=", deadline)
                case 7:
                        print("ADDITION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.addition(a, b, deadline)
                case 8:
                        print("MULTIPLICATION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.multiplication(a, b, deadline)
                case 9:
                        print("DIVISION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.division(a, b, deadline)

            end_time = time.perf_counter()
            time_elapsed_ms = int((end_time - start_time)*1000)

            print(f"Time Elapsed {time_elapsed_ms}ms")
            print(f"Response {response}")

            if (not response.success):
                time.sleep(5)

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

    for i in range(threads):
        thread = threading.Thread(target=main, args=(address, )).start()