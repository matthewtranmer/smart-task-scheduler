from lib import taskoffloader
import base64, gzip

offloader = taskoffloader.TaskOffloader(("10.45.1.34", 2004))

test_data = b"This is some data that needs to be compressed. " * 5
response = offloader.compress(test_data, deadline_ms=1000)
print(response)

response = offloader.decompress(response.value, deadline_ms=1000)
print(response)
# response = offloader.decompress(response.value, deadline=1000)
# print("Decompressed data:", response.value)


# input bytes -> b64 bytes -> b64 string -> b64 bytes -> bytes -> compress

# container produces bytes
# 