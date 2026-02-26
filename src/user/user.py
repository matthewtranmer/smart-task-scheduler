import socket, time, threading, json, random, os, traceback, sys, base64
from lib import edge_pb2, net, taskoffloader
from lib.scheduler import Tasks 

def main(address):
    try:
        offloader = taskoffloader.TaskOffloader(address)

        with open("src/user/test_data/ballon.png", "rb") as f:
            image_bytes = f.read()

        response = offloader.object_count(image_bytes, 2000)
        print(f"Got response: {response}")

        return

        with open("src/user/test_data/ballon.png", "rb") as f:
                image_bytes = f.read()

        while True:
            deadline = random.randint(200, 3000)
            print(f"deadline: {deadline}")
        #     deadline = 1

            start_time = time.perf_counter()

            tasks = [
                Tasks.BANANA_QUALITY_RIPENESS,
                Tasks.ORANGE_QUALITY_RIPENESS,
                Tasks.DETECT_HUMAN,
                Tasks.FRUIT_DEFECTS,
                Tasks.FRUIT_SIZE,
                Tasks.CLASSIFY_FRUIT,  
                Tasks.OBJECT_COUNT,          
            ]

            task_id = random.choice(tasks)

            # task_id = 7
            match task_id:
                case Tasks.DETECT_HUMAN:
                        print("DETECT HUMAN")
                        response = offloader.detectHuman(image_bytes, deadline)
                case Tasks.CLASSIFY_FRUIT:
                        print("CLASSIFY FRUIT")
                        response = offloader.classifyFruit(image_bytes, deadline)
                case Tasks.FRUIT_QUALITY:
                        print("FRUIT QUALITY")
                        response = offloader.fruitQuality(image_bytes, deadline)
                case Tasks.COMPRESSION:
                        print("COMPRESSION")
                        data = "This is some data that needs to be compressed. " * 20
                        response = offloader.compress(data, deadline)
                case Tasks.DECOMPRESSION:
                        print("DECOMPRESSION")
                        data = "This is some data that needs to be compressed. " * 20
                        response = offloader.decompress(data, deadline)
                case Tasks.ENCRYPTION:
                        print("ENCRYPTION")
                        response = offloader.encrypt("keykeykeykeykey1", "This is some plaintext data to be encrypted.", deadline)
                case Tasks.DECRYPTION:
                        print("DECRYPTION")
                        response = offloader.decrypt("keykeykeykeykey1", "U2FsdGVkX1+I3V6Y5G6u1g6X9s6jZ0bX5Zl5r8QvV3I=", deadline)
                case Tasks.ORANGE_QUALITY_RIPENESS:
                        print("ORANGE_QUALITY_RIPENESS")
                        response = offloader._test_orange_ripeness(image_bytes, deadline)
                case Tasks.BANANA_QUALITY_RIPENESS:
                        print("BANANA_QUALITY_RIPENESS")
                        response = offloader._test_banana_ripeness(image_bytes, deadline)

                case Tasks.FRUIT_DEFECTS:
                        print("FRUIT_DEFECTS")
                        response = offloader.fruit_defects(image_bytes, deadline)
                case Tasks.FRUIT_SIZE:
                        print("FRUIT_SIZE")
                        response = offloader.fruit_size(image_bytes, deadline)

                case Tasks.ADDITION:
                        print("ADDITION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.addition(a, b, deadline)
                case Tasks.MULTIPLICATION:
                        print("MULTIPLICATION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.multiplication(a, b, deadline)
                case Tasks.DIVISION:
                        print("DIVISION")

                        a = random.randint(1, 99)
                        b = random.randint(1, 99)

                        response = offloader.division(a, b, deadline)

            end_time = time.perf_counter()
            time_elapsed_ms = int((end_time - start_time)*1000)

            print(f"Time Elapsed {time_elapsed_ms}ms")
            print(f"Response {response}")

            if (not response.success):
                # Task dropped
                if (response.code == 551):
                    for i in range(30):
                        print("TASK DROPPED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
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