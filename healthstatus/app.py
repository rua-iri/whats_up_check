
import json
import os
import traceback
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


dynamo_client = boto3.client("dynamodb")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE")


def convert_dynamo_dict(item):

    if not item:
        return item

    converted_items = {}

    for key, value in item.items():
        converted_items[key] = list(value.values())[0]

    return converted_items


def get_dynamo_record(req_id: str):
    item_key = {
        "id": {
            "S": req_id
        }
    }

    item: dict = dynamo_client.get_item(
        Key=item_key,
        TableName=DYNAMO_TABLE,
        ProjectionExpression="site_url, success_count, fail_count"
    ).get("Item")

    item = convert_dynamo_dict(item)

    return item


def dispatch(event, context):
    logger.info(event)
    logger.info(event.get("queryStringParameters"))

    query_string: dict = event.get("queryStringParameters")

    if not query_string:
        raise Exception("No query string provided")

    req_id: str | None = query_string.get("id")

    if not req_id:
        raise Exception("No query string provided")

    health_check_item = get_dynamo_record(req_id)

    logger.info(health_check_item)

    if not health_check_item:
        return {
            "statusCode": 404,
            "body": json.dumps(
                {"error": "No Records found"}
            )
        }

    fail_count = health_check_item.get("fail_count")
    success_count = health_check_item.get("success_count")

    logger.info(f"Success Count: {success_count}")
    logger.info(f"Fail Count: {fail_count}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            health_check_item
        )
    }


def lambda_handler(event, context):
    try:
        return dispatch(event, context)

    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "An error occurred"}
            )
        }
