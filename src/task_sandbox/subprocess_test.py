import subprocess, json

data = {"a": 1, "b": 5}
json_data = json.dumps(data)

result = subprocess.run(["bash", "task_sandbox/tasks/addition/addition.sh", json_data], capture_output=True, text=True)
print(int(result.stdout.strip()))