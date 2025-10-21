#!/bin/bash

# This script launches the infrastructure as code deployment process.
# Make sure yu have the necessary permissions and environment variables set before running.

echo "Starting Infrastructure as Code deployment..."

# Initialize the IaC tool (e.g., Terraform, Ansible, etc.)
echo "Initializing IaC tool..."
terraform init
if [ $? -ne 0 ]; then
    echo "Initialization failed. Exiting."
    exit 1
fi

# Validate the configuration files
echo "Validating configuration files..."
terraform validate
if [ $? -ne 0 ]; then
    echo "Validation failed. Exiting."
    exit 1
fi

# Apply the configuration to deploy the infrastructure
echo "Applying configuration to deploy infrastructure..."
terraform apply -auto-approve
if [ $? -ne 0 ]; then
    echo "Deployment failed. Exiting."
    exit 1
fi

echo "Infrastructure deployed successfully."   


# Upload data to S3 bucket after successful deployment
echo "Uploading dataset to S3 bucket..."
aws s3 cp ../ml_model/raw_dataset/conveyor_fault_dataset.csv s3://predictive-maintenance-data-1/raw_dataset/conveyor_fault_dataset.csv
if [ $? -ne 0 ]; then
    echo "S3 upload failed. Please check your AWS credentials and bucket permissions."
    exit 1
fi
echo "Dataset uploaded successfully to S3."
exit 0

