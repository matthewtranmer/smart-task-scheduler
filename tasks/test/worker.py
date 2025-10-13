import sys, json

for line in sys.stdin:
    line = line.strip()
    if len(line) == 0:
        continue

    job = json.loads(line)
    
    job_id = job.get("id")
    payload = job.get("payload")

    # Do whatever you want here:
    result = {"echo": payload}

    # Send result back
    print(json.dumps({"id": job_id, "result": result}), flush=True)
