import glob
import psutil

# Return a list of logical CPU IDs, one per physical core,
# by taking the first sibling from each core's thread_siblings_list
def getPhysicalCpuIds():
    cpu_files = glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology/thread_siblings_list")

    first_siblings = []
    seen = set()

    for f in cpu_files:
        with open(f) as fh:
            # thread_siblings_list can look like "0,16" or "0-1" on some systems
            raw = fh.read().strip()

        # Normalize ranges like "4-5" into ["4", "5"]
        parts = []
        for token in raw.split(","):
            if "-" in token:
                a, b = token.split("-")
                parts.extend(map(str, range(int(a), int(b) + 1)))
            else:
                parts.append(token)

        first = int(parts[0])
        if first not in seen:
            seen.add(first)
            first_siblings.append(first)

    return first_siblings

# Returns the amount of system memory in MiB
def getSystemMemoryMB():
    return psutil.virtual_memory().total // 1024 // 1024