import time, sys, json, socket, os, subprocess

def wasteTime(iterations):
    index = 0
    for i in range(iterations):
        index += 1

def multiplication(a, b):
    return_val = a * b
    wasteTime(25_000_000)
    return return_val

def division(a, b):
    return_val = a / b
    wasteTime(50_000_000)
    return return_val

def main():
    for line in sys.stdin:
        line = line.strip()
        if len(line) == 0:
            continue

        input = json.loads(line)

        # Select task
        match input["task_name"]:
            case "addition":
                result = subprocess.run(["/bin/sh", "/app/tasks/addition/addition.sh", input["task_params"]], capture_output=True, text=True)
                response = result.stdout
            case "multiplication":
                response = multiplication(input["a"], input["b"])
            case "division":
                response = division(input["a"], input["b"])

        # Send result back
        print(response, flush=True)

if __name__ == "__main__":
    main()


