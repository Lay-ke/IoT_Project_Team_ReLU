import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('bedrock-agentcore', region_name='eu-west-1')

def lambda_handler(event, context):
    try:
        # Detect event source
        if "Records" in event and "s3" in event["Records"][0]:
            # ---- S3 Trigger ----
            record = event["Records"][0]
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            logger.info(f"S3 event triggered for: s3://{bucket}/{key}")

            s3 = boto3.client("s3")
            obj = s3.get_object(Bucket=bucket, Key=key)
            content = obj["Body"].read().decode("utf-8")
            logger.info(f"Loaded file content from S3: {content[:200]}...")

            # Parse predictions from file
            try:
                data = json.loads(content)
                predictions = data.get("predictions", [])
                if not predictions:
                    raise ValueError("No predictions found in file.")
            except Exception as e:
                logger.error(f"Invalid JSON in S3 object: {e}")
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON in S3 object"})
                }

            # Use predictions as the payload
            payload = json.dumps({"predictions": predictions})

        else:
            # ---- API Gateway Event ----
            try:
                body = json.loads(event.get("body", "{}"))
                logger.info(f"API body: {body}")
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON in body"})
                }

            prompt = body.get("prompt")
            if not prompt:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Missing 'prompt' in request body"})
                }

            payload = json.dumps({"prompt": prompt})

        # ---- Invoke Bedrock Agent ----
        response = client.invoke_agent_runtime(
            agentRuntimeArn="arn:aws:bedrock-agentcore:eu-west-1:771826808190:runtime/relu_agent-K1lW4rCNbV",
            runtimeSessionId="dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmt",
            payload=payload,
            qualifier="DEFAULT"
        )

        # Read response from the Bedrock agent
        response_body = response["response"].read()
        response_data = json.loads(response_body)
        logger.info(f"Agent Response: {json.dumps(response_data, indent=2)}")

        return {
            "statusCode": 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            },
            "body": json.dumps(response_data)
        }

    except Exception as e:
        logger.exception("Error invoking Bedrock Agent")
        return {
            "statusCode": 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            },
            "body": json.dumps({"error": str(e)})
        }
