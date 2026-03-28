import socket, time, threading, json, random, os, traceback, sys, base64, gzip
from lib import edge_pb2, net, taskoffloader
from lib.task_definitions import TaskIDs

lock = threading.Lock()

dropped_tasks = 0
deadlines_missed = 0
tasks_executed = 0

problem_tasks = []

with open("src/cloud-debug-service/orange_removed_bg.png", "rb") as f:
        image_bytes = f.read()

uncompressed_data = b"This is some data that needs to be compressed. " * 20
compressed_data = gzip.compress(uncompressed_data)

def send_task(address, task_id, deadline_ms):
    global tasks_executed, dropped_tasks, deadlines_missed

    start_time = time.perf_counter()

    offloader = taskoffloader.TaskOffloader(address)

    match task_id:
        case TaskIDs.DETECT_HUMAN:
            task_name = "DETECT HUMAN"
            response = offloader.detectHuman(image_bytes, deadline_ms)
        case TaskIDs.CLASSIFY_FRUIT:
            task_name = "CLASSIFY FRUIT"
            response = offloader.classifyFruit(image_bytes, deadline_ms)
        case TaskIDs.COMPRESSION:
            task_name = "COMPRESSION"
            response = offloader.compress(uncompressed_data, deadline_ms)
        case TaskIDs.DECOMPRESSION:
            task_name = "DECOMPRESSION"
            response = offloader.decompress(compressed_data, deadline_ms)
        case TaskIDs.ENCRYPTION:
            task_name = "ENCRYPTION"
            response = offloader.encrypt(os.urandom(32), b"This is some plaintext data to be encrypted.", deadline_ms)
        case TaskIDs.DECRYPTION:
            task_name = "DECRYPTION"
            response = offloader.decrypt(
                b'g\x94\xfb\x13\x8a\xc7\x86\x8a\x85UW\xa0\xed\xb1\xf9Z\xe8\xed\xd7\x1c\r\x08\x18\xc5\xea\r\x98\x1c\x87\x03\xd6\xe0',
                b'FMeXkkYSYAXkMgtrRsvUm6+OedmjgLpAJ8a+MreO+MWIlRNRzPCekBqJ',
                deadline_ms
            )
        case TaskIDs.OBJECT_COUNT:
            task_name = "OBJECT_COUNT"
            response = offloader.object_count(image_bytes, deadline_ms)
        case TaskIDs.OBJECT_COUNT:
            task_name = "OBJECT_COUNT"
            response = offloader.object_count(image_bytes, deadline_ms)
        case TaskIDs.OBJECT_COUNT:
            task_name = "OBJECT_COUNT"
            response = offloader.object_count(image_bytes, deadline_ms)
        case TaskIDs.BANANA_QUALITY_RATING:
            task_name = "BANANA_QUALITY_RATING"
            response = offloader.banana_quality_rating(image_bytes, deadline_ms)
        case TaskIDs.ORANGE_QUALITY_RATING:
            task_name = "ORANGE_QUALITY_RATING"
            response = offloader.orange_quality_rating(image_bytes, deadline_ms)

        case _:
            while True:
                print(f"Task ID {task_id} not found")

    end_time = time.perf_counter()
    time_elapsed_ms = int((end_time - start_time)*1000)

    print(f"""Task name {task_name}\nTime elapsed {time_elapsed_ms}ms\nResponse {response}""")

    with lock:
        problem = False
        text = f"Task name {task_name}\nTime elapsed {time_elapsed_ms}ms\nDeadline {deadline_ms}ms\n"

        if (not response.success):
            # Task dropped
            if (response.code == 551):
                text += "TASK DROPPED\n"
                dropped_tasks += 1
                problem = True


        # Deadline is missed if execution time is above 10% of the deadline
        if time_elapsed_ms > deadline_ms * 1.1:
            text += "DEADLINE MISSED\n"
            deadlines_missed += 1
            problem = True

        tasks_executed += 1

        if problem:
            problem_tasks.append(text)

def main(address, task_dataset_file_path):
    try:
        with open(task_dataset_file_path, "r") as f_dataset:
            dataset = json.load(f_dataset)

        current_time = 0.0

        for task in dataset:
            task_id = task["task_id"]
            deadline_ms = int(task["deadline_seconds"] * 1000)
            start_time_seconds = task["start_time_seconds"]

            if start_time_seconds > current_time:
                time.sleep(start_time_seconds - current_time)
                current_time = start_time_seconds

            print(f"Executing task with id {task_id}")
            threading.Thread(target=send_task, args=(address, task_id, deadline_ms)).start()
            
    except Exception as e:
        print("CLIENT SIDE EXECEPTION")
        traceback.print_exc()
        os._exit(-1)

    time.sleep(5)

    print("Task simulation finished!")
    print(f"Tasks executed: {tasks_executed}")
    print(f"Tasks dropped: {dropped_tasks}")
    print(f"Deadlines missed: {deadlines_missed}")

    for message in problem_tasks:
        print(message)
        print("-----------------------------------")
        

if __name__ == "__main__":
    address = None
    threads = 1

    if len(sys.argv) > 1:
        address = sys.argv[1]
        address = address.split(":")
        address[1] = int(address[1])
        address = tuple(address)

    if len(sys.argv) > 2:
        task_dataset_file_path = sys.argv[2]

    t0 = time.perf_counter()
    main(address, task_dataset_file_path)
    t1 = time.perf_counter()

    print(f"Time elapsed {t1 - t0}s")