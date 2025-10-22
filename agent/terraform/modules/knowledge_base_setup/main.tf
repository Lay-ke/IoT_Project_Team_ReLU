resource "null_resource" "update_opensearch_policy" {
  provisioner "local-exec" {
    command = <<-EOT
      CURRENT_USER=$(aws sts get-caller-identity --query Arn --output text)
      POLICY_VERSION=$(aws opensearchserverless get-access-policy --name ${var.policy_name} --type data --query 'accessPolicyDetail.policyVersion' --output text --region ${var.region})
      aws opensearchserverless update-access-policy \
        --name ${var.policy_name} \
        --type data \
        --policy-version "$POLICY_VERSION" \
        --policy "[{\"Rules\":[{\"Resource\":[\"collection/${var.collection_name}\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:DeleteCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DescribeCollectionItems\"],\"ResourceType\":\"collection\"},{\"Resource\":[\"index/${var.collection_name}/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:DeleteIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"],\"ResourceType\":\"index\"}],\"Principal\":[\"${var.kb_role_arn}\",\"$CURRENT_USER\"]}]" \
        --region ${var.region}
      sleep 60
    EOT
  }
}

resource "null_resource" "create_knowledge_base" {
  triggers = {
    collection_arn = var.collection_arn
    kb_role_arn    = var.kb_role_arn
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.root}/scripts
      python3 -m venv venv 2>/dev/null || true
      ./venv/bin/pip install -q opensearch-py boto3 2>/dev/null || true
      ./venv/bin/python3 create_knowledge_base.py "${var.collection_arn}" "${var.kb_role_arn}"
    EOT
  }

  depends_on = [null_resource.update_opensearch_policy]
}
