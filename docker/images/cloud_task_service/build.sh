#!/bin/bash
set -euo pipefail

echo "Please run from project root"
docker build -f docker/images/cloud_task_service/dockerfile -t smart-task-scheduler/cloud-task-service .
