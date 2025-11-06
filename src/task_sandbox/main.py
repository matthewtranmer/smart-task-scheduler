import time, sys, json, socket, os, subprocess, traceback, base64

from tasks.detect_human.detect_human import detectHuman
# from tasks.classify_fruit.classify_fruit import classifyFruit
# from tasks.fruit_quality.fruit_quality import fruitQuality
from tasks.compression.compression import compress
from tasks.encryption.encryption import encrypt

# Test tasks
from tasks.addition.addition import addition
from tasks.multiplication.multiplication import multiplication
from tasks.division.division import division

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
                        image_bytes_b64 = parameters["img_bytes"].encode()
                        image_bytes = base64.decodebytes(image_bytes_b64)

                        result = detectHuman(image_bytes)
                        # pass
                    case 1:
                        # result = classifyFruit(parameters["img_bytes"])
                        pass
                    case 2:
                        # result = fruitQuality(parameters["img_bytes"])
                        pass
                    case 3:
                        result = compress(parameters["data"])
                    case 4:
                        result = encrypt(parameters["key"], parameters["plaintext"])
                    # Test tasks
                    case 100:
                        result = addition(parameters["a"], parameters["b"])
                    case 101:
                        result = multiplication(parameters["a"], parameters["b"])
                    case 102:
                        result = division(parameters["a"], parameters["b"])

                response = {"value": result, "inputID": input["inputID"]}
                print(json.dumps(response), flush=True)  

        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    main()



# {"id": 0, "params": "{\"a\": 2, \"b\": 20}"}