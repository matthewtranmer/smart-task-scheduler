import sys

first_arg = sys.argv[1]
print(first_arg)

with open(f"/sys/fs/cgroup/system.slice/docker-{first_arg}.scope/memory.peak", "r") as f:
    peak_bytes = int(f.read())

peak_mib = peak_bytes / 1024 / 1024

print(peak_mib)