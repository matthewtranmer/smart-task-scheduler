import socket, time, threading, json, random, os, traceback, sys, base64, gzip
from lib import edge_pb2, net, taskoffloader
from lib.task_definitions import TaskIDs

def main(address):
    try:
        offloader = taskoffloader.TaskOffloader(address)

        with open("src/user/test_data/orange.png", "rb") as f:
            image_bytes = f.read()

        t0 = time.perf_counter()
        response = offloader.REMOVE_BG_TEST(image_bytes, 3000)
        t1 = time.perf_counter()

        # print(response)
        print(f"Execution time: {(t1-t0) * 1000}ms")

        return


        # while True:
        #     key = os.urandom(32)
        #     result = offloader.encrypt(key, b"ExecutedOnEdge", 1000)
        #     print(key)
        #     print(result.value)
        #     return

        # return

        # print("ENCRYPTION")
        # response = offloader.encrypt(, b"This is some plaintext data to be encrypted.", 1000)
        # print(response)
        # return

        with open("src/cloud-debug-service/orange_removed_bg.png", "rb") as f:
                image_bytes = f.read()

        uncompressed_data = b"This is some data that needs to be compressed. " * 20
        compressed_data = gzip.compress(uncompressed_data)

        while True:
            # deadline = random.randint(1000, 3000)
            deadline = 5000

            print(f"deadline: {deadline}")

            start_time = time.perf_counter()

            tasks = [
                # TaskIDs.DETECT_HUMAN,
                # TaskIDs.CLASSIFY_FRUIT,
                # TaskIDs.COMPRESSION,
                # TaskIDs.DECOMPRESSION,
                # TaskIDs.ENCRYPTION,
                # TaskIDs.DECRYPTION,
                # TaskIDs.OBJECT_COUNT,
                # TaskIDs.BANANA_QUALITY_RATING,
                TaskIDs.ORANGE_QUALITY_RATING,
            ]

            task_id = random.choice(tasks)

            match task_id:
                case TaskIDs.DETECT_HUMAN:
                    task_name = "DETECT HUMAN"
                    response = offloader.detectHuman(image_bytes, deadline)
                case TaskIDs.CLASSIFY_FRUIT:
                    task_name = "CLASSIFY FRUIT"
                    response = offloader.classifyFruit(image_bytes, deadline)
                case TaskIDs.COMPRESSION:
                    task_name = "COMPRESSION"
                    response = offloader.compress(uncompressed_data, deadline)
                case TaskIDs.DECOMPRESSION:
                    task_name = "DECOMPRESSION"
                    response = offloader.decompress(compressed_data, deadline)
                case TaskIDs.ENCRYPTION:
                    task_name = "ENCRYPTION"
                    response = offloader.encrypt(os.urandom(32), b"This is some plaintext data to be encrypted.", deadline)
                case TaskIDs.DECRYPTION:
                    task_name = "DECRYPTION"
                    response = offloader.decrypt(
                        b'g\x94\xfb\x13\x8a\xc7\x86\x8a\x85UW\xa0\xed\xb1\xf9Z\xe8\xed\xd7\x1c\r\x08\x18\xc5\xea\r\x98\x1c\x87\x03\xd6\xe0',
                        b'FMeXkkYSYAXkMgtrRsvUm6+OedmjgLpAJ8a+MreO+MWIlRNRzPCekBqJ',
                        deadline
                    )
                case TaskIDs.OBJECT_COUNT:
                    task_name = "OBJECT_COUNT"
                    response = offloader.object_count(image_bytes, deadline)
                case TaskIDs.BANANA_QUALITY_RATING:
                    task_name = "BANANA_QUALITY_RATING"
                    response = offloader.banana_quality_rating(image_bytes, deadline)
                case TaskIDs.ORANGE_QUALITY_RATING:
                    task_name = "ORANGE_QUALITY_RATING"
                    response = offloader.orange_quality_rating(image_bytes, deadline)

                case _:
                    while True:
                        print("ERR!!!!!!!!!!!!!!!!")

            end_time = time.perf_counter()
            time_elapsed_ms = int((end_time - start_time)*1000)

            print(f"""Task name {task_name}\nTime elapsed {time_elapsed_ms}ms\nResponse {response}
                """)

            if (not response.success):
                # Task dropped
                if (response.code == 551):
                    for i in range(30):
                        print("TASK DROPPED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    time.sleep(5)

            break

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