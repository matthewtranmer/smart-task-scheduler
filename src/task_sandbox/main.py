import time, sys, json, socket, os, subprocess, traceback

def wasteTime(iterations):
    index = 0
    for i in range(iterations):
        index += 1

def addition(a, b):
    return_val = a + b
    wasteTime(12_000_000)
    return return_val

def multiplication(a, b):
    return_val = a * b
    wasteTime(25_000_000)
    return return_val

def division(a, b):
    return_val = a / b
    wasteTime(50_000_000)
    return return_val

def main():
    while True:
        try:
            for line in sys.stdin:
                line = line.strip()
                if len(line) == 0:
                    continue

                input = json.loads(line)
                parameters = json.loads(input["params"])

                # Select task
                match input["id"]:
                    case 0:
                        # print(input["params"], file=sys.stderr)
                        result = addition(parameters["a"], parameters["b"])
                    case 100:
                        print("TEST", flush=True)
                        continue

                response = {"value": result, "inputID": input["inputID"]}
                print(json.dumps(response), flush=True)  

                # Send result back
                # print(response, flush=True)
        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    main()



# {"id": 0, "params": "{\"a\": 2, \"b\": 20}"}