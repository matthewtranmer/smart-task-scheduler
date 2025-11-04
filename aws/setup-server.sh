#!/bin/bash
# Install requirements
sudo apt-get update -y
sudo apt-get install -y unzip curl python3 python3-pip git

# Install AWS cmdline util to get deploy key
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Parameters
SSM_PARAM_NAME="smart-task-scheduler-deploy-key"
USER="ubuntu"
REPO_URL="https://github.com/matthewtranmer/smart-task-scheduler"
APP_DIR="/home/$APP_USER/smart-task-scheduler"

# Get Deploy Key from AWS parameter store
DEPLOY_KEY=$(
    aws ssm get-parameter \
  --name "$SSM_PARAM_NAME" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text \
)

# Setup SSH key
sudo -u "$USER" mkdir -p /home/$USER/.ssh
echo "$DEPLOY_KEY" | sudo -u "$USER" tee /home/$USER/.ssh/id_ed25519 > /dev/null
# Change file permissions
sudo -u "$USER" chmod 600 /home/$USER/.ssh/id_ed25519

# Add GitHub to known hosts
sudo -u "$USER" ssh-keyscan github.com >> /home/$USER/.ssh/known_hosts

# Clone repo
sudo -u "$USER" git clone "$REPO_URL" "$APP_DIR" || {
  # If already exists - pull latest
  cd "$APP_DIR"
  sudo -u "$USER" git pull
}

# Create Virtual Environment
python3 -m venv "$APP_DIR/env"

# Install requirements
pip3 install -r "$APP_DIR/requirements.txt"

# Start server
