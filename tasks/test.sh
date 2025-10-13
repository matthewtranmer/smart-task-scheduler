docker run -d --rm --cpuset-cpus="2" --cpu-quota=100000 --name demo addition

PIDS=$(docker top demo -eo pid | awk 'NR>1{printf "%s,", $1}' | sed 's/,$//')

sudo perf stat -e cycles,instructions,task-clock -p "$PIDS"