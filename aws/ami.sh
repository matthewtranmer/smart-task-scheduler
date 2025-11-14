#!/bin/bash
set -euo pipefail

echo "STARTING SERVER SETUP SCRIPT -------------------------------------------------------------------------------------"

export DEBIAN_FRONTEND=noninteractive
APT_OPTS='-y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold'

echo "Installing basic dependencies -------------------------------------------------------------------------------------"

# Install requirements
sudo apt-get update -y
sudo apt-get install $APT_OPTS unzip curl python3 python3-pip git

# Install AWS cmdline util to get deploy key
if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI not found - installing -------------------------------------------------------------------------------------"
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip -o awscliv2.zip
  sudo ./aws/install
  rm -rf awscliv2.zip aws
else
  echo "AWS CLI already installed - skipping -------------------------------------------------------------------------------------"
fi


# Create Virtual Environment
sudo apt-get update -y
sudo apt-get install -y python3-venv 


# Install docker (only if not already installed)
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found - installing -------------------------------------------------------------------------------------"
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
  echo "Docker already installed - skipping -------------------------------------------------------------------------------------"
fi

sudo docker pull matthewtranmer/sandbox_base