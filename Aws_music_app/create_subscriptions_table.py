import boto3

# Initialize the DynamoDB resource (make sure the region is correct)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Create the Subscriptions table
table = dynamodb.create_table(
    TableName='Subscriptions',
    KeySchema=[
        {
            'AttributeName': 'user_email',
            'KeyType': 'HASH'  # Partition key
        },
        {
            'AttributeName': 'song_title',
            'KeyType': 'RANGE'  # Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'user_email',
            'AttributeType': 'S'  # String type
        },
        {
            'AttributeName': 'song_title',
            'AttributeType': 'S'  # String type
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

# Wait until the table exists
table.wait_until_exists()

print("Table status:", table.table_status)
