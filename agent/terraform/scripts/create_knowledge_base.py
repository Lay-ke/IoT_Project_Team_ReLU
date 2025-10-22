#!/usr/bin/env python3
import boto3
import time
import sys
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def create_knowledge_base(project_name, environment, kb_role_arn, collection_arn, s3_bucket_arn, prefixes):
    region = boto3.Session().region_name or 'eu-west-1'
    bedrock = boto3.client('bedrock-agent', region_name=region)
    aoss = boto3.client('opensearchserverless', region_name=region)
    
    collection_id = collection_arn.split('/')[-1]
    response = aoss.batch_get_collection(ids=[collection_id])
    collection_endpoint = response['collectionDetails'][0]['collectionEndpoint']
    
    print(f"Collection endpoint: {collection_endpoint}")
    print("Creating OpenSearch index...")
    
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, 'aoss')
    
    print("Waiting for permissions to propagate...")
    time.sleep(90)
    
    os_client = OpenSearch(
        hosts=[{'host': collection_endpoint.replace('https://', ''), 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    index_name = 'bedrock-knowledge-base-default-index'
    index_body = {
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw"
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                "AMAZON_BEDROCK_METADATA": {"type": "text"}
            }
        }
    }
    
    if not os_client.indices.exists(index=index_name):
        os_client.indices.create(index=index_name, body=index_body)
        print(f"Index created: {index_name}")
    
    print("Creating Knowledge Base...")
    kb_response = bedrock.create_knowledge_base(
        name=f"{project_name}-kb-v2-{environment}",
        roleArn=kb_role_arn,
        knowledgeBaseConfiguration={
            'type': 'VECTOR',
            'vectorKnowledgeBaseConfiguration': {
                'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'
            }
        },
        storageConfiguration={
            'type': 'OPENSEARCH_SERVERLESS',
            'opensearchServerlessConfiguration': {
                'collectionArn': collection_arn,
                'vectorIndexName': index_name,
                'fieldMapping': {
                    'vectorField': 'bedrock-knowledge-base-default-vector',
                    'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                    'metadataField': 'AMAZON_BEDROCK_METADATA'
                }
            }
        }
    )
    
    kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
    print(f"Knowledge Base created: {kb_id}")
    
    for i, prefix in enumerate(prefixes, 1):
        bedrock.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"{project_name}-kb-v2-ds{i}-{environment}",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {'bucketArn': s3_bucket_arn, 'inclusionPrefixes': [prefix]}
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {'maxTokens': 300, 'overlapPercentage': 20}
                }
            }
        )
        print(f"Data source {i} created for: {prefix}")
    
    return kb_id

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python create_knowledge_base.py <collection_arn>")
        sys.exit(1)
    
    kb_id = create_knowledge_base(
        project_name='faultcast',
        environment='dev',
        kb_role_arn=sys.argv[2] if len(sys.argv) > 2 else None,
        collection_arn=sys.argv[1],
        s3_bucket_arn='arn:aws:s3:::predictive-maintenance-feature-store',
        prefixes=['knowledge-base-inference/', 'maintenance-schedules/']
    )
    
    print(f"\n✅ Knowledge Base ID: {kb_id}")
    
    # Update SSM parameter
    import subprocess
    import json
    
    # Get SSM prefix from terraform output
    result = subprocess.run(
        ['terraform', 'output', '-json'],
        cwd='/home/michael/Downloads/agentic/agent/terraform',
        capture_output=True,
        text=True
    )
    
    ssm_prefix = '/faultcast/v2'  # default
    if result.returncode == 0:
        outputs = json.loads(result.stdout)
        if 'ssm_parameter_prefix' in outputs:
            ssm_prefix = outputs['ssm_parameter_prefix']['value']
    
    subprocess.run([
        'aws', 'ssm', 'put-parameter',
        '--name', f'{ssm_prefix}/knowledge-base-id',
        '--value', kb_id,
        '--type', 'SecureString',
        '--overwrite',
        '--region', 'eu-west-1'
    ])
    print(f"✅ SSM parameter updated: {ssm_prefix}/knowledge-base-id")
