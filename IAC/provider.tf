terraform {
  backend "s3" {
    bucket  = "relu-terra-state"
    key     = "terraform-state/prod/terraform.tfstate"
    region  = "eu-west-1"
    encrypt = true
    # use_lockfile = false
    acl = "bucket-owner-full-control"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.15.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "3.7.2"
    }
  }
}