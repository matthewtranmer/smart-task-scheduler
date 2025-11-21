#!/bin/bash
set -euo pipefail

echo 1
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 965851311996.dkr.ecr.eu-north-1.amazonaws.com
echo 2
docker tag smart-task-scheduler/cloud-task-service:latest 965851311996.dkr.ecr.eu-north-1.amazonaws.com/smart-task-scheduler/cloud-task-service:latest
echo 3
docker push 965851311996.dkr.ecr.eu-north-1.amazonaws.com/smart-task-scheduler/cloud-task-service:latest
echo 4