#!/usr/bin/env python3
"""
Flask Dashboard – Task Scheduling View (single-file)

What's new (per your request)
- KPIs: latest task arrival time, task deadline hit rate %, average processing time
- Online nodes table: node id, tasks assigned, memory %, CPU %
- Task stats table: task (name/id), average processing time, assigned node id
- Clean Bootstrap layout + Chart.js sparklines
- Simple JSON APIs you can wire to your scheduler

Run
$ pip install flask
$ python app.py  # http://127.0.0.1:5000

Swap the fake data generators with your real data feeds.
"""
from __future__ import annotations

import os
import random
import datetime as dt
from dataclasses import dataclass
from statistics import mean

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

random.seed(7)

# -------------------------------
# Fake data (replace with real)
# -------------------------------
@dataclass
class TaskRecord:
    task_id: str
    node_id: str
    duration_ms: int
    created_at: dt.datetime
    deadline_hit: bool


def fake_now() -> dt.datetime:
    return dt.datetime.utcnow().replace(microsecond=0)


def generate_task_records(n: int = 120) -> list[TaskRecord]:
    now = fake_now()
    tasks: list[TaskRecord] = []
    for i in range(n):
        created = now - dt.timedelta(seconds=random.randint(5, 3600))
        task_name = random.choice(["resize", "thumbnail", "transcode", "inference", "etl", "backup"])
        node_id = random.choice(["edge-01", "edge-02", "core-01", "gpu-01"])  # your nodes here
        dur = random.choice([180, 260, 420, 750, 1200, 1800, 2200, 3200])
        deadline_hit = random.random() > 0.1  # ~90% hit
        tasks.append(TaskRecord(task_name, node_id, dur, created, deadline_hit))
    return tasks


def generate_nodes(tasks: list[TaskRecord]) -> list[dict]:
    nodes = {}
    for t in tasks:
        nodes.setdefault(t.node_id, {"node_id": t.node_id, "tasks_assigned": 0, "cpu_pct": 0.0, "mem_pct": 0.0})
        nodes[t.node_id]["tasks_assigned"] += 1
    # fake cpu/mem
    for n in nodes.values():
        n["cpu_pct"] = round(20 + random.random() * 70, 1)
        n["mem_pct"] = round(15 + random.random() * 75, 1)
    return sorted(nodes.values(), key=lambda x: x["node_id"])


# cache a small dataset for the demo
_DATA = generate_task_records(160)

# -----------------
# API
# -----------------
@app.get("/")
def home():
    return render_template("template.html")


@app.get("/api/overview")
def api_overview():
    """Return KPI-style overview including arrival times, hit rate, avg proc time."""
    window = int(request.args.get("window", 30))
    # Use last `window` tasks by recency
    tasks = sorted(_DATA, key=lambda t: t.created_at, reverse=True)[:window]

    latest_arrival = max(t.created_at for t in tasks) if tasks else None
    avg_proc = int(mean(t.duration_ms for t in tasks)) if tasks else 0
    hit_rate = round(100 * (sum(1 for t in tasks if t.deadline_hit) / max(1, len(tasks))), 1)

    # simple sparklines
    tasks_sorted = sorted(tasks, key=lambda t: t.created_at)
    labels = [t.created_at.strftime("%H:%M:%S") for t in tasks_sorted]
    arrivals_ms = [int((tasks_sorted[i].created_at - tasks_sorted[i-1].created_at).total_seconds()*1000) if i>0 else 0 for i in range(len(tasks_sorted))]
    hit_vals = [100 if t.deadline_hit else 0 for t in tasks_sorted]
    avg_vals = []
    run = []
    for t in tasks_sorted:
        run.append(t.duration_ms)
        avg_vals.append(int(mean(run)))

    return jsonify({
        "latest_arrival_iso": latest_arrival.isoformat() + "Z" if latest_arrival else None,
        "deadline_hit_rate_pct": hit_rate,
        "avg_processing_ms": avg_proc,
        "arrivals": {"labels": labels, "values_ms": arrivals_ms},
        "hit_rate": {"labels": labels, "values_pct": hit_vals},
        "avg_proc": {"labels": labels, "values_ms": avg_vals},
    })


@app.get("/api/nodes")
def api_nodes():
    return jsonify(generate_nodes(_DATA))


@app.get("/api/task_stats")
def api_task_stats():
    by_task = {}
    for t in _DATA:
        k = (t.task_id, t.node_id)
        by_task.setdefault(k, []).append(t.duration_ms)
    rows = [
        {"task_id": k[0], "node_id": k[1], "avg_processing_ms": int(mean(v))}
        for k, v in by_task.items()
    ]
    rows.sort(key=lambda r: (r["task_id"], r["node_id"]))
    return jsonify(rows)


@app.get("/api/table")
def api_table():
    limit = max(1, min(500, int(request.args.get("limit", 50))))
    rows = sorted(_DATA, key=lambda t: t.created_at, reverse=True)[:limit]
    return jsonify({
        "rows": [
            {
                "task_id": t.task_id,
                "node_id": t.node_id,
                "duration_ms": t.duration_ms,
                "created_at": t.created_at.isoformat() + "Z",
                "deadline_hit": t.deadline_hit,
            }
            for t in rows
        ]
    })


@app.get("/healthz")
def healthz():
    return ("ok", 200)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
