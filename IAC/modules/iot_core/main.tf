resource "aws_iot_topic_rule" "rule" {
  name        = "MyRule"
  description = "Example rule"
  enabled     = true
  sql         = "SELECT * FROM 'predictive-maintenance/sensor-data-1'"
  sql_version = "2016-03-23"

  lambda {
    function_arn = var.lambda_function_arn
  }

}


data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["iot.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "myrole" {
  name               = "myrole"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "aws_iam_policy_document" "mypolicy" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [var.lambda_function_arn]
  }
}

resource "aws_iam_role_policy" "mypolicy" {
  name   = "mypolicy"
  role   = aws_iam_role.myrole.id
  policy = data.aws_iam_policy_document.mypolicy.json
}