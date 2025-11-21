import gzip

def compress(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9)

def decompress(compressed_data: bytes) -> bytes:
    return gzip.decompress(compressed_data)