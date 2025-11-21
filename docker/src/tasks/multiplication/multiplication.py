def wasteTime(iterations):
    index = 0
    for i in range(iterations):
        index += 1

def multiplication(a, b):
    return_val = a + b
    wasteTime(25_000_000)
    return return_val