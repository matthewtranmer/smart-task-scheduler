#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
APT_OPTS='-y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"'

# Install requirements
sudo apt-get update -y
sudo apt-get install $APT_OPTS unzip curl python3 python3-pip git

# Install AWS cmdline util to get deploy key
if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI not found - installing..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip -o awscliv2.zip
  sudo ./aws/install
  rm -rf awscliv2.zip aws
else
  echo "AWS CLI already installed - skipping."
fi

# Parameters
SSM_PARAM_NAME="smart-task-scheduler-deploy-key"
USER="ubuntu"
REPO_URL="git@github.com:matthewtranmer/smart-task-scheduler.git"
APP_DIR="/home/$USER/smart-task-scheduler"

# Get Deploy Key from AWS parameter store
DEPLOY_KEY=$(
    aws ssm get-parameter \
  --name "$SSM_PARAM_NAME" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text \
)

# Setup SSH key
echo "Setting up SSH deploy key..."
sudo -u "$USER" mkdir -p /home/$USER/.ssh
echo "$DEPLOY_KEY" | sudo -u "$USER" tee /home/$USER/.ssh/id_ed25519 > /dev/null
# Change file permissions
sudo -u "$USER" chmod 600 /home/$USER/.ssh/id_ed25519

# Add GitHub to known hosts
echo "Adding GitHub to known hosts..."
sudo -u "$USER" ssh-keyscan github.com >> /home/$USER/.ssh/known_hosts

# Clone repo
sudo -u "$USER" git clone "$REPO_URL" "$APP_DIR" || {
  # If already exists - pull latest
  cd "$APP_DIR"
  sudo -u "$USER" git pull
}

# Create Virtual Environment
sudo apt-get update -y
sudo apt-get install -y python3-venv 

sudo -u "$USER" python3 -m venv "$APP_DIR/env"

# Install requirements into the venv
sudo -u "$USER" "$APP_DIR/env/bin/pip" install --upgrade pip
sudo -u "$USER" "$APP_DIR/env/bin/pip" install -r "$APP_DIR/requirements.txt"

# Install docker (only if not already installed)
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found - installing..."
  sudo apt update
  sudo apt install $APT_OPTS ca-certificates curl gnupg lsb-release -y
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt update
  sudo apt install $APT_OPTS docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
  sudo usermod -aG docker $USER
else
  echo "Docker already installed - skipping."
fi

# Start server (as ubuntu, from app dir)
echo "Starting task server..."
cd "$APP_DIR"
sudo -u "$USER" "$APP_DIR/run/task-server-cloud.sh"