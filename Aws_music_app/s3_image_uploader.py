import boto3
import json
import requests
from io import BytesIO

# Replace with your S3 bucket name
S3_BUCKET = 'music-app-2025a1'
JSON_FILE = '2025a1.json'

# Initialize the S3 client (set your region if needed)
s3_client = boto3.client('s3', region_name='us-east-1')

# Load the JSON data
with open(JSON_FILE, 'r') as file:
    data = json.load(file)

# Handle JSON structure: either a list of songs or a dictionary with a "songs" key
if isinstance(data, dict) and 'songs' in data:
    songs = data['songs']
elif isinstance(data, list):
    songs = data
else:
    raise ValueError("Unexpected JSON structure. Expected a list or a dictionary with a 'songs' key.")

# Process each song's image_url
for song in songs:
    image_url = song.get('img_url')
    if not image_url:
        print(f"No image URL found for '{song.get('title', 'Unknown Title')}'. Skipping...")
        continue

    try:
        # Download the image using requests
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Create a file-like object from the response content
        image_data = BytesIO(response.content)

        # Construct a unique S3 key (file name) for the image.
        # Here, we use the song title and artist, replacing spaces with underscores.
        title = song.get('title', 'untitled').replace(' ', '_')
        artist = song.get('artist', 'unknown').replace(' ', '_')
        s3_key = f"images/{title}_{artist}.jpg"

        # Upload the image file-like object to S3
        s3_client.upload_fileobj(image_data, S3_BUCKET, s3_key)
        print(f"Uploaded image for '{song.get('title')}' to S3 as '{s3_key}'.")
    except Exception as e:
        print(f"Error processing image for '{song.get('title', 'Unknown Title')}': {e}")

print("All images processed.")
