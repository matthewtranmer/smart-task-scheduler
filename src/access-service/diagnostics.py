import threading
from lib import scheduler as s
from lib import edge_pb2
from lib import task_definitions

class Diagnostics:
    JOB_HISTORY_SIZE = 200
    job_history = []

    measurement_interval_s = 0

    cloud_task_count = 0
    cloud_percentage = 0
    cloud_tasks_per_second = 0
    edge_tasks_per_second = 0

    task_count = 0
    tasks_per_second = 0

    processing_times = 0
    processing_times_count = 0
    average_processing_time = 0

    deadline_hit_rate = 0
    deadline_misses = 0
    deadline_hits = 0

    task_processing_times = {}

    def __init__(self, measurement_interval_s, scheduler, display=False):
        self.display = display
        self.measurement_interval_s = measurement_interval_s
        self.scheduler = scheduler
        self._mainLoop()

    def _mainLoop(self):
        self._calculateCloudPercentage()
        self._calculateAverageProcessingTimes()
        self._calculateTasksPerSecond()
        self._calculateDeadlineHitRate()
        self.scheduler.calculateResourceUsage(self.measurement_interval_s)

        self.cloud_task_count = 0
        
        threading.Timer(self.measurement_interval_s, self._mainLoop).start()

    def addJob(self, task: edge_pb2.Task, scheduled_node: s.ScheduledNode, processing_time_ms: int):
        self.incrementProcessingTime(processing_time_ms, task.taskID)

        deadline_hit = False
        if (processing_time_ms < task.deadline_ms):
            deadline_hit = True
        
        self.addDeadlineTask(deadline_hit)
        
        if (scheduled_node.node_type == s.NodeType.EDGE):
            assigned_node = f"edge-{self.scheduler.getNodeID(scheduled_node.address)}"
        else:
            self.cloud_task_count += 1
            assigned_node = "cloud"

        self.job_history.append({
            "name": str(task.taskID),
            "assigned_node": assigned_node,
            "processing_time": processing_time_ms,
            "deadline": task.deadline_ms,
            "deadline_hit": deadline_hit
        })

        if (len(self.job_history) >= self.JOB_HISTORY_SIZE):
            self.job_history.pop(0)

    def _calculateCloudPercentage(self):
        if self.task_count <= 0:
            self.cloud_percentage = 0
        else:
            self.cloud_percentage = round(self.cloud_task_count / self.task_count * 100, 1)

        if (self.display):
            print(f"Cloud percentage: {self.cloud_percentage}%")

    def _calculateDeadlineHitRate(self):
        task_count = self.deadline_misses + self.deadline_hits
        if task_count == 0:
            self.deadline_hit_rate = 0
        else:
            self.deadline_hit_rate = round((self.deadline_hits / task_count) * 100, 3)

        self.deadline_hits = 0
        self.deadline_misses = 0

        if (self.display):
            print(f"Deadline hit rate: {self.deadline_hit_rate}%")

    def _calculateAverageProcessingTimes(self):
        if (self.processing_times_count == 0):
            self.average_processing_time = 0
        else:
            self.average_processing_time = round(self.processing_times / self.processing_times_count, 3)
        
        self.processing_times = 0
        self.processing_times_count = 0

        # Calculate averages on a per task basis
        for task_id in self.task_processing_times:
            processing_times = self.task_processing_times[task_id]["processing_times"]
            processing_times_count = self.task_processing_times[task_id]["processing_times_count"]

            if processing_times_count == 0:
                self.task_processing_times[task_id]["average_processing_time"] = 0
            else:
                self.task_processing_times[task_id]["average_processing_time"] = round(processing_times / processing_times_count, 3)

            self.task_processing_times[task_id]["processing_times"] = 0
            self.task_processing_times[task_id]["processing_times_count"] = 0

        if (self.display):
            print(f"Average processing time: {self.average_processing_time}")

    # Called every task_measurement_interval_s
    def _calculateTasksPerSecond(self):
        self.tasks_per_second = round(self.task_count / self.measurement_interval_s, 3)
        print(self.cloud_task_count)
        self.cloud_tasks_per_second = round(self.cloud_task_count / self.measurement_interval_s, 3)
        self.edge_tasks_per_second = round((self.task_count - self.cloud_task_count) / self.measurement_interval_s, 3)

        self.task_count = 0
        self.cloud_task_count = 0
        self.edge_task_count = 0

        if (self.display):
            print(f"Tasks per second: {self.tasks_per_second}")

    def incrementTasks(self, count=1):
        self.task_count += count

    def tasksPerSecond(self) -> int:
        return self.tasks_per_second
    
    def incrementProcessingTime(self, processing_time, task_id):
        self.processing_times += processing_time
        self.processing_times_count += 1

        if task_id not in self.task_processing_times:
            self.task_processing_times[task_id] = {
                "processing_times": processing_time,
                "processing_times_count": 1,
                "average_processing_time": 0
            }
        else:
            self.task_processing_times[task_id]["processing_times"] += processing_time
            self.task_processing_times[task_id]["processing_times_count"] += 1

    def addDeadlineTask(self, did_hit_deadline: bool):
        if (did_hit_deadline):
            self.deadline_hits += 1
        else:
            self.deadline_misses += 1

    def sampleAllDiagnosticData(self):
        nodes = self.scheduler.getNodes()
        online_nodes = []

        for node in nodes:
            data = {
                "name": f"edge-{node["id"]}",
                "ip": node["address"][0],
                "port":node["address"][1],
                "assigned_tasks": node["assigned_tasks"],
                "cpu": node["cpu_usage"],
                "memory": round((node["memory"] - node["memory_available"]) / node["memory"] * 100, 2)
            }

            online_nodes.append(data)
        
        task_averages = []
        for task_id in self.task_processing_times:
            data = {}

            data["name"] = f"{task_definitions.task_names[task_id]}"
            data["processing_time"] = self.task_processing_times[task_id]["average_processing_time"]

            task_averages.append(data)

        data = {
            "task_arrival_rate": self.tasks_per_second,
            "deadline_hit_rate": self.deadline_hit_rate,
            "average_processing_time": self.average_processing_time,
            "online_nodes": online_nodes,
            "task_averages": task_averages,
            "recent_jobs": self.job_history,
            "cloud_percentage": self.cloud_percentage,
            "edge_arrival_rate": self.edge_tasks_per_second,
            "cloud_arrival_rate": self.cloud_tasks_per_second,
        }

        return data