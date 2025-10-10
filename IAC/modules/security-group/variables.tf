variable "vpc_id" {
  description = "The ID of the VPC where the security group will be created"
  type        = string
}

variable "from_port" {
  description = "The starting port for the security group rule"
  type        = number
  default     = 80
}

variable "to_port" {
  description = "The ending port for the security group rule"
  type        = number
  default     = 80
}

variable "cidr_blocks" {
  description = "The CIDR blocks to allow traffic from"
  type        = list(string)
}