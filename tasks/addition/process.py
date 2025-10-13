import time, sys, json

def wasteTime(iterations):
    index = 0
    for i in range(iterations):
        index += 1

def perform(a, b):
    return_val = a + b
    wasteTime(12_000_000)
    return return_val

def getInput():
    input_data = sys.stdin.read()

    try:
        payload = {}
        if input_data.strip():
            payload = json.loads(input_data) 

        return payload

    except json.JSONDecodeError:
        print(json.dumps({"error": "invalid JSON"}))
        sys.exit(1)

def main():
    input = getInput()
    # input = {"a": 55, "b":500}
    response = perform(input["a"], input["b"])
    print(response)

if __name__ == "__main__":
    main()


# My PC
#100_000_000 - 2.5 seconds
#50_000_000 - 1.25
#25_000_000 - 0.75
#12_000_000 - 0.30


