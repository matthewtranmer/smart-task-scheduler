container_id = "beec99c80bdd6a810992f0a7b8b2d969859ac736682903b947a494f3953fb5ec"

with open(f"/sys/fs/cgroup/system.slice/docker-{container_id}.scope/memory.peak", "r") as f:
    peak_bytes = int(f.read())

peak_mib = peak_bytes / 1024 / 1024

print(peak_mib)