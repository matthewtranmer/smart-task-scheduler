import gzip

def compress(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9)

def decompress(compressed_data: bytes) -> bytes:
    return gzip.decompress(compressed_data)

text = b"apple dot com " * 10000
compressed_data = compress(text)

decompressed_data = decompress(compressed_data)
print(f"Original len: {len(text)}")
print(f"Compressed len: {len(compressed_data)}")