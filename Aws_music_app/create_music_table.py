import boto3

# Create a DynamoDB resource. Make sure to set the correct region.
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Define the table name
table_name = 'Music'

# Create the Music table with 'title' as the partition key and 'artist' as the sort key
try:
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'title',  # Partition key
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'artist',  # Sort key
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'title',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'artist',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    print("Creating table. Please wait...")
    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    print(f"Table '{table_name}' created successfully!")

except Exception as e:
    print("Error creating table:", e)
