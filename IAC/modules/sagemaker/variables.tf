variable "sagemaker_domain_name" {
  description = "The name of the SageMaker domain"
  type        = string

}

variable "sagemaker_execution_role_arn" {
  description = "The ARN of the SageMaker execution role"
  type        = string

}

variable "vpc_id" {
  description = "The ID of the VPC where the SageMaker domain will be created"
  type        = string

}

variable "subnet_id" {
  description = "The ID of the subnet within the VPC"
  type        = list(string)

}

variable "sagemaker_distribution_image_arn" {
  description = "The ARN of the SageMaker image to use"
  type        = string

}