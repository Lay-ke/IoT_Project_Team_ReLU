import boto3
import json

s3 = boto3.client('s3')

def list_all_objects(bucket_name, prefix=''):
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    all_objects = []
    for page in pages:
        if 'Contents' in page:
            all_objects.extend(page['Contents'])

    return all_objects

def lambda_handler(event, context):
    bucket_name = 'predictive-maintenance-data-1'
    prefix = 'conveyor_batches/' 

    # Fetch all objects (across all pages)
    all_files = list_all_objects(bucket_name, prefix)

    if not all_files:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'No JSON files found'})
        }

    json_files = [obj for obj in all_files if obj['Key'].endswith('.json')]

    # Sort by LastModified (most recent last)
    json_files.sort(key=lambda x: x['LastModified'])

    # Get latest 10 files
    latest_files = json_files[-10:]

    results = []

    for file in latest_files:
        key = file['Key']
        try:
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            parsed = json.loads(content)
        except Exception as e:
            parsed = {'error': f'Could not read {key}', 'details': str(e)}

        results.append({
            'key': key,
            'last_modified': file['LastModified'].isoformat(),
            'content': parsed
        })

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(results)
    }
