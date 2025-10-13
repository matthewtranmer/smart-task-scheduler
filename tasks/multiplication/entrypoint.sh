#!/usr/bin/env bash

if [ -z "$RUNTIME_US" ]; then
    echo "No runtime set — running normally."
    python3 -u process.py
else
    exec chrt -d \
        --sched-runtime  "${RUNTIME_US}" \
        --sched-deadline "${DEADLINE_US}" \
        --sched-period   "${DEADLINE_US}" \
        0 python3 -u process.py 
fi


