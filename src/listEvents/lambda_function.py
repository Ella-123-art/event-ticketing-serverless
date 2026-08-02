import boto3
import json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Events')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def lambda_handler(event, context):
    response = table.scan()
    events = response.get('Items', [])

    for e in events:
        capacity = e.get('capacity', 0)
        registered = e.get('registeredCount', 0)
        if registered >= capacity:
            e['status'] = 'Full'
        elif registered >= 3:
            e['status'] = 'Limited'
        else:
            e['status'] = 'Available'

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(events, default=decimal_default)
    }