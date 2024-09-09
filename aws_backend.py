import json
from datetime import datetime, timedelta

from aiobotocore.session import get_session

DYNAMODB_TABLE_NAME = "your_dynamodb_table_name"

AWS_REGION = "your_aws_region"
S3_BUCKET_NAME = "your_s3_bucket_name"
CACHE_EXPIRY = timedelta(minutes=5)

async def store_weather_data(city: str, data: dict) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{city}_{timestamp}.json"

    # Use aiobotocore to interact with S3 asynchronously
    session = get_session()
    async with session.create_client('s3', region_name=AWS_REGION) as s3:
        await s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
            Body=json.dumps(data)
        )
    return f"s3://{S3_BUCKET_NAME}/{filename}"

async def log_weather_event(city: str, s3_url: str):
    session = get_session()
    async with session.create_client('dynamodb', region_name=AWS_REGION) as dynamodb:
        await dynamodb.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item={
                'city': {'S': city},
                'timestamp': {'S': datetime.utcnow().isoformat()},
                's3_url': {'S': s3_url}
            }
        )


async def get_cached_weather_data(city: str) -> dict:
    session = get_session()
    async with session.create_client('s3', region_name=AWS_REGION) as s3:
        now = datetime.utcnow()
        response = await s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"{city}_")
        if 'Contents' in response:
            for obj in response['Contents']:
                # Extract the timestamp from the object key
                key = obj['Key']
                timestamp_str = key.split("_")[1].split(".json")[0]
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

                # If the file is within the cache expiry period, return the cached data
                if now - timestamp < CACHE_EXPIRY:
                    cached_obj = await s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
                    content = await cached_obj['Body'].read()
                    return json.loads(content)
    return None
