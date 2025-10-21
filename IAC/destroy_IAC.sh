#!/bin/bash

# This script launches the infrastructure as code deployment process.
# Make sure you have the necessary permissions and environment variables set before running.

echo "Destroying Infrastructure as Code deployment..."

# Initialize the IaC tool (e.g., Terraform, Ansible, etc.)
echo "Initializing IaC tool..."
terraform init
if [ $? -ne 0 ]; then
    echo "Initialization failed. Exiting."
    exit 1
fi

# Destroy the deployed infrastructure
echo "Destroying deployed infrastructure..."
terraform destroy -auto-approve
if [ $? -ne 0 ]; then
    echo "Destruction failed. Exiting."
    exit 1
fi

echo "Infrastructure destroyed successfully."
exit 0