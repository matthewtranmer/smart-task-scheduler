import threading
from lib import scheduler as s


class Diagnostics:
    JOB_HISTORY_SIZE = 200
    job_history = []

    measurement_interval_s = 0

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
        self._calculateAverageProcessingTimes()
        self._calculateTasksPerSecond()
        self._calculateDeadlineHitRate()
        
        threading.Timer(self.measurement_interval_s, self._mainLoop).start()

    def addJob(self, task_id, address, processing_time_ms, deadline_ms, deadline_hit):
        self.job_history.append({
            "name": s.Tasks.getName(task_id),
            "assigned_node": self.scheduler.getNodeID(address),
            "processing_time": round(processing_time_ms, 3),
            "deadline": deadline_ms,
            "deadline_hit": deadline_hit
        })

        if (len(self.job_history) >= self.JOB_HISTORY_SIZE):
            self.job_history.pop(0)

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
        self.task_count = 0

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
                "assigned_tasks": 0,
                "cpu": 0,
                "memory": 0
            }

            online_nodes.append(data)
        
        task_averages = []
        for task_id in self.task_processing_times:
            data = {}

            data["name"] = s.Tasks.getName(task_id)
            data["processing_time"] = self.task_processing_times[task_id]["average_processing_time"]

            task_averages.append(data)

        data = {
            "task_arrival_rate": self.tasks_per_second,
            "deadline_hit_rate": self.deadline_hit_rate,
            "average_processing_time": self.average_processing_time,
            "online_nodes": online_nodes,
            "task_averages": task_averages,
            "recent_jobs": self.job_history
        }

        return data