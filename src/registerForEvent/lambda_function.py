import boto3
import json
import uuid
from datetime import datetime, timezone
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
events_table = dynamodb.Table('Events')
registrations_table = dynamodb.Table('Registrations')

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    event_id = body.get('eventId')
    email = body.get('email')

    if not event_id or not email:
        return _response(400, {'error': 'eventId and email are required'})

    event_item = events_table.get_item(Key={'eventId': event_id}).get('Item')
    if not event_item:
        return _response(404, {'error': 'Event not found'})

    if event_item.get('registeredCount', 0) >= event_item.get('capacity', 0):
        return _response(409, {'error': 'Event is full'})

    try:
        events_table.update_item(
            Key={'eventId': event_id},
            UpdateExpression='SET registeredCount = registeredCount + :inc',
            ConditionExpression='registeredCount < #cap',
            ExpressionAttributeNames={'#cap': 'capacity'},
            ExpressionAttributeValues={':inc': 1}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return _response(409, {'error': 'Event is full'})
        raise

    registration_id = str(uuid.uuid4())
    registrations_table.put_item(Item={
        'registrationId': registration_id,
        'eventId': event_id,
        'email': email,
        'registeredAt': datetime.now(timezone.utc).isoformat()
    })

    return _response(201, {'registrationId': registration_id, 'message': 'Registration successful'})

def _response(status_code, body_dict):
    return {
        'statusCode': status_code,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(body_dict)
    }