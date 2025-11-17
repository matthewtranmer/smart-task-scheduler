#!/bin/bash
set -euo pipefail

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
echo "Setting up SSH deploy key -------------------------------------------------------------------------------------"
sudo -u "$USER" mkdir -p /home/$USER/.ssh
echo "$DEPLOY_KEY" | sudo -u "$USER" tee /home/$USER/.ssh/id_ed25519 > /dev/null
# Change file permissions
sudo -u "$USER" chmod 600 /home/$USER/.ssh/id_ed25519

# Add GitHub to known hosts
echo "Adding GitHub to known hosts -------------------------------------------------------------------------------------"
sudo -u "$USER" ssh-keyscan github.com >> /home/$USER/.ssh/known_hosts

# Clone repo
echo "Cloning repository -------------------------------------------------------------------------------------"
sudo -u "$USER" git clone "$REPO_URL" "$APP_DIR" || {
  # If already exists - pull latest
  cd "$APP_DIR"
  sudo -u "$USER" git pull
}

# Create Virtual Environment
echo "Creating Python virtual environment -------------------------------------------------------------------------------------"
sudo -u "$USER" python3 -m venv "$APP_DIR/env"

# Install requirements into the venv
echo "Installing Python dependencies into venv -------------------------------------------------------------------------------------"
sudo -u "$USER" "$APP_DIR/env/bin/pip" install --upgrade pip
sudo -u "$USER" "$APP_DIR/env/bin/pip" install -r "$APP_DIR/requirements.txt"

# Build docker image
echo "Building sandbox docker image -------------------------------------------------------------------------------------"
sudo -u "$USER" docker build "$APP_DIR/src/task_sandbox" -t task_sandbox 

chmod +x "$APP_DIR/run/task-server-cloud.sh"

# Create the systemd service
cat > /etc/systemd/system/task-server-cloud.service << EOF
[Unit]
Description=Task server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/run/task-server-cloud.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable task-server-cloud.service
systemctl start task-server-cloud.service