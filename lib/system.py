import glob
import psutil
import platform
import subprocess
import glob

# Return a list of logical CPU IDs, one per physical core,
# by taking the first sibling from each core's thread_siblings_list.
# Linux and Mac implementations
def getPhysicalCpuIds():
    system = platform.system()

    if system == "Linux":
        # --- Linux path ---
        cpu_files = glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology/thread_siblings_list")
        first_siblings = []
        seen = set()
        for f in cpu_files:
            with open(f) as fh:
                raw = fh.read().strip()
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

    elif system == "Darwin":
        # --- macOS path ---
        # macOS doesn't expose /sys; use sysctl to get core counts
        try:
            physical = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"]).strip())
            logical = int(subprocess.check_output(["sysctl", "-n", "hw.logicalcpu"]).strip())
        except Exception as e:
            raise RuntimeError("Failed to get CPU info on macOS") from e

        # macOS doesn't expose thread-to-core mapping, so we just assume
        # 1 logical per physical core → take first N logical CPUs.
        cpus = list(range(physical))
        return cpus

    else:
        raise NotImplementedError(f"Unsupported OS: {system}")

# Returns the amount of system memory in MiB
def getSystemMemoryMB():
    return psutil.virtual_memory().total // 1024 // 1024