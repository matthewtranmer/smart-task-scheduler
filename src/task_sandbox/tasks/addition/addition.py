import sys,json

def wasteTime(iterations):
    index = 0
    for i in range(iterations):
        index += 1

def addition(a, b):
    return_val = a + b
    wasteTime(12_000_000)
    return return_val

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        json_in = sys.argv[1]

    input_data = json.loads(json_in)
    print(addition(input_data["a"], input_data["b"]))