import boto3
import json

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Music')

json_file = '2025a1.json'

try:
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Debug print to inspect data structure
    print("Loaded data type:", type(data))
    print("Loaded data:", data)

    # If data is a dictionary and contains a key 'songs', extract it.
    if isinstance(data, dict):
        if 'songs' in data:
            songs = data['songs']
        else:
            raise ValueError("Expected a key 'songs' in the JSON file, but got keys: " + str(list(data.keys())))
    elif isinstance(data, list):
        songs = data
    else:
        raise ValueError("Expected a list of songs or a dictionary containing 'songs' key in the JSON file.")

    # Ensure that songs is a list before proceeding
    if not isinstance(songs, list):
        raise ValueError("Expected a list of songs in the JSON file.")

    # Insert each song into the DynamoDB table
    for song in songs:
        response = table.put_item(
            Item={
                'title': song.get('title'),
                'artist': song.get('artist'),
                'year': song.get('year'),
                'album': song.get('album'),
                'img_url': song.get('img_url', "")  # default to empty string if not provided
            }
        )
        print(f"Inserted '{song.get('title')}' by {song.get('artist')} successfully.")

    print("All data loaded successfully!")

except Exception as e:
    print("Error loading data:", e)
