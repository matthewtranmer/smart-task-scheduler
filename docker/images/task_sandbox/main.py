import sys, json, traceback
from src import task

def main():
    while True:
        try:
            for line in sys.stdin:
                line = line.strip()
                if len(line) == 0:
                    continue

                input = json.loads(line)
                parameters = json.loads(input["params"])

                result = task.run_task(input["id"], parameters)

                response = {"value": result, "inputID": input["inputID"]}
                print(json.dumps(response), flush=True)  

        except Exception:
            print(222222222)
            exception = traceback.format_exc()
            response = {"value": exception}
            print(json.dumps(response), file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()