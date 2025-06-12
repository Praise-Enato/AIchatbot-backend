import os

import boto3

DYNAMODB_URL = os.getenv("DYNAMODB_URL", None)
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")  # Fallback to us-east-1

dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_URL, region_name=REGION)
answers_table = dynamodb.Table("quiz-answers")
