resource "aws_sagemaker_domain" "relu_domain" {
  domain_name = var.sagemaker_domain_name
  auth_mode   = "IAM"
  vpc_id      = var.vpc_id
  subnet_ids  = var.subnet_id

  default_user_settings {
    execution_role = var.sagemaker_execution_role_arn

    studio_web_portal   = "DISABLED"
    default_landing_uri = "app:JupyterServer:"
  }

  default_space_settings {
    execution_role = var.sagemaker_execution_role_arn
  }
}


resource "aws_sagemaker_user_profile" "relu_user" {
  domain_id         = aws_sagemaker_domain.relu_domain.id
  user_profile_name = "reluUser"
}