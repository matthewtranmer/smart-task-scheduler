import os
os.environ["PYTHONPATH"] = "~/repos/smart-task-scheduler"

import random, math, pprint, json
from lib.task_definitions import TaskIDs
import sys

# Create a list of tasks execeuted in order
# Each task must have a name, an ID, the time in which it will be
# executed (in seconds from start time) and a random deadline in a 
# range.
# Different tasks have different inputs - if a task expects an image,
# specify a random image ID in the range 0-200. If a task expects
# a string of bytes, make a random string in a specific range.
# For the decompression task, make a random compressed string.
# For the decryption task, make a random encrypted string and a random
# key.
# Write the output to a JSON file

task_definitions = [
   {
       "task_name": "human_detection",
       "task_id": TaskIDs.DETECT_HUMAN,
       "deadline_range_seconds": (0.3, 0.7),
   }, 
   {
       "task_name": "classify_fruit",
       "task_id": TaskIDs.CLASSIFY_FRUIT,
       "deadline_range_seconds": (1, 2),
   },
   {
       "task_name": "object_count",
       "task_id": TaskIDs.OBJECT_COUNT,
       "deadline_range_seconds": (0.4, 3.0),
   },
   {
       "task_name": "encryption",
       "task_id": TaskIDs.ENCRYPTION,
       "deadline_range_seconds": (0.3, 3.0),
   },
   {
       "task_name": "decryption",
       "task_id": TaskIDs.DECRYPTION,
       "deadline_range_seconds": (0.3, 3.0),
   },
   {
       "task_name": "compression",
       "task_id": TaskIDs.COMPRESSION,
       "deadline_range_seconds": (0.2, 3.0),
   },
   {
       "task_name": "decompression",
       "task_id": TaskIDs.DECOMPRESSION,
       "deadline_range_seconds": (0.2, 3.0),
   },
   {
       "task_name": "banana_quality_rating",
       "task_id": TaskIDs.BANANA_QUALITY_RATING,
       "deadline_range_seconds": (0.9, 2.5),
   },
   {
       "task_name": "orange_quality_rating",
       "task_id": TaskIDs.ORANGE_QUALITY_RATING,
       "deadline_range_seconds": (0.9, 2.5),
   }
]

def create_tasks(frequency_hz, task_definition, task_list, time):
    period = 1 / frequency_hz
    deadline_range_seconds = task_definition["deadline_range_seconds"]

    for i in range(frequency_hz):
        task_data = {
            "task_name": task_definition["task_name"],
            "task_id": task_definition["task_id"],
            "start_time_seconds": 0.0,
            "deadline_seconds": 0.0,
            "input": ""
        }

        task_data["start_time_seconds"] = float(time + (i * period))
    
        task_data["deadline_seconds"] = random.uniform(
            deadline_range_seconds[0],
            deadline_range_seconds[1]
        )

        task_list.append(task_data)

def main(multipler, output_file_name):
    output_dataset = []

    # Iteration = 1 second
    for time in range(120):
        current_tasks = []    

        for task_definition in task_definitions:
            match task_definition["task_name"]:
                case "human_detection":
                    # 30% chance of being called
                    if (random.uniform(0, 1) > 0.7):
                        create_tasks(
                            frequency_hz=int(30 * multipler),
                            task_definition=task_definition,
                            task_list=current_tasks,
                            time=time
                        )

                case "classify_fruit":
                    # Called between 20 and 30 times per second
                    frequency_hz=random.randint(int(20 * multipler), int(30 * multipler))

                    create_tasks(
                        frequency_hz=frequency_hz,
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

                    # banana_quality_rating
                    create_tasks(
                        frequency_hz=frequency_hz//2,
                        task_definition=task_definitions[7],
                        task_list=current_tasks,
                        time=time
                    )

                    # orange_quality_rating
                    create_tasks(
                        frequency_hz=frequency_hz//2,
                        task_definition=task_definitions[8],
                        task_list=current_tasks,
                        time=time
                    )

                case "object_count":
                    create_tasks(
                        frequency_hz=random.randint(int(10 * multipler), int(20 * multipler)),
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

                case "encryption":
                    create_tasks(
                        frequency_hz=int(10 * multipler),
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

                case "decryption":
                    create_tasks(
                        frequency_hz=int(10 * multipler),
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

                case "compression":
                    create_tasks(
                        frequency_hz=int(40 * multipler),
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

                case "decompression":
                    create_tasks(
                        frequency_hz=int(40 * multipler),
                        task_definition=task_definition,
                        task_list=current_tasks,
                        time=time
                    )

        current_tasks.sort(key=lambda x: x["start_time_seconds"])

        for task in current_tasks:
            output_dataset.append(task)


    with open(f"other/dataset/{output_file_name}.json", "w+") as file:
        json.dump(output_dataset, file)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        multiplier = float(sys.argv[1])
        output_file_name = sys.argv[2]

    main(multiplier, output_file_name)