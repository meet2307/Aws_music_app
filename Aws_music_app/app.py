from flask import Flask, render_template, request, redirect, url_for, flash,session
import boto3
from boto3.dynamodb.conditions import Attr, Key

app = Flask(__name__)
app.secret_key = 'AdocziPo+7Kqivi6rlIHkfCc+AW0DkqrRtluWyT0'  # Set a secure key

# Configuration for S3
BUCKET_NAME = 'music-app-2025a1'  # Change to your actual bucket name
S3_REGION = 'us-east-1'

# DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Tables (make sure these exist in your account)
login_table = dynamodb.Table('login_table')
music_table = dynamodb.Table('Music')
subscription_table = dynamodb.Table('Subscriptions')
# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)

def get_presigned_url(s3_key, expires_in=3600):
    # Prepend "images/" if missing.
    if s3_key and not s3_key.startswith("images/"):
        s3_key = "images/" + s3_key
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        app.logger.debug("Generated presigned URL for key %s: %s", s3_key, url)
        print("Generated presigned URL for key", s3_key, ":", url)  # Temporary print
        return url
    except Exception as e:
        app.logger.error("Error generating presigned URL for key %s: %s", s3_key, e)
        print("Error generating presigned URL for key", s3_key, ":", e)
        return None


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()  # remove extra whitespace
        password = request.form.get('password').strip()
        # Retrieve the user record from DynamoDB
        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')
        print("Debug: Retrieved user from DynamoDB:", user)
        if user is None:
            flash("User not found. Please register.")
            return redirect(url_for('login'))
        # Optionally compare trimmed values if needed
        if user.get('password', '').strip() == password:
            session['user'] = user  # save the entire user object in session
            print("Debug: User stored in session:", session['user'])
            return redirect(url_for('main'))
        else:
            flash("Email or password is invalid")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('user_name')
        password = request.form.get('password')

        # Check if the email already exists in the Login table
        response = login_table.get_item(Key={'email': email})
        if 'Item' in response:
            flash("The email already exists.")
            return redirect(url_for('register'))
        else:
            # Insert new user into the Login table
            login_table.put_item(
                Item={
                    'email': email,
                    'user_name': username,
                    'password': password
                }
            )
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/main')
def main():
    # Check if the user is logged in
    user = session.get('user')
    if not user:
        flash("Please log in first")
        return redirect(url_for('login'))

    # Query the Subscriptions table to get subscriptions for this user
    try:
        subscriptions_response = subscription_table.query(
            KeyConditionExpression=Key('user_email').eq(user['email'])
        )
        subscriptions = subscriptions_response.get('Items', [])
    except Exception as e:
        flash("Error retrieving subscriptions: " + str(e))
        subscriptions = []

    # Pass subscriptions along with other data to the main template
    return render_template('main.html', user=user, query_results=session.pop('query_results', None),
                           subscriptions=subscriptions)

@app.route('/query', methods=['POST'])
def query():
    # Get search parameters from the form
    title = request.form.get('title', '').strip()
    artist = request.form.get('artist', '').strip()
    album = request.form.get('album', '').strip()
    year_str = request.form.get('year', '').strip()

    # Build filter expressions; only add expressions for fields with user input
    filter_expressions = []

    if title:
        filter_expressions.append(Attr('title').contains(title))
    if artist:
        filter_expressions.append(Attr('artist').contains(artist))
    if album:
        filter_expressions.append(Attr('album').contains(album))
    if year_str:
        try:
            year = int(year_str)
            if year < 1900 or year > 2100:
                flash("Please enter a valid year between 1900 and 2100.")
                return redirect(url_for('main'))
            year = int(year_str)
            filter_expressions.append(Attr('year').eq(year_str))
            app.logger.debug("Querying for year: %s", year)
        except ValueError:
            flash("Year must be a valid number.")
            return redirect(url_for('main'))

    # Ensure at least one condition is provided; if not, flash an error.
    if not filter_expressions:
        flash("Please enter at least one query criterion.")
        return redirect(url_for('main'))

    # Combine filter expressions using AND logic.
    combined_filter = filter_expressions[0]
    for expr in filter_expressions[1:]:
        combined_filter = combined_filter & expr

    try:
        # Perform a scan on the Music table using the combined filter expression
        response = music_table.scan(FilterExpression=combined_filter)
        results = response.get('Items', [])
        if results:
            for song in results:
                if song.get('image_url'):
                    presigned = get_presigned_url(song['image_url'])
                    song['image_url'] = presigned if presigned else song['image_url']
        session['query_results'] = results
        return redirect(url_for('main'))

    except Exception as e:
        flash("An error occurred while querying: " + str(e))
        return redirect(url_for('main'))

    # Retrieve subscriptions as well so they don’t disappear
    user = session.get('user')
    try:
        subscriptions_response = subscription_table.query(
            KeyConditionExpression=Key('user_email').eq(user['email'])
        )
        subscriptions = subscriptions_response.get('Items', [])
    except Exception as e:
        flash("Error retrieving subscriptions: " + str(e))
        subscriptions = []

    return render_template('main.html', user=user, query_results=results, subscriptions=subscriptions)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    user = session.get('user')
    if not user:
        flash("Please log in first.")
        return redirect(url_for('login'))

    # Get the song details from the form
    title = request.form.get('title')
    artist = request.form.get('artist')
    album = request.form.get('album')
    year_str = request.form.get('year', '').strip()
    image_url = request.form.get('image_url')

    try:
        year = int(year_str) if year_str else None
    except ValueError:
        year = None

    try:
        # Check if the subscription for this song already exists for the user.
        existing = subscription_table.get_item(
            Key={
                'user_email': user['email'],
                'song_title': title
            }
        )
        if 'Item' in existing:
            flash(f"You have already subscribed to '{title}'.")
            return redirect(url_for('main'))

        # Insert the subscription record into the Subscriptions table.
        subscription_table.put_item(
            Item={
                'user_email': user['email'],
                'song_title': title,
                'artist': artist,
                'album': album,
                'year': year,
                'image_url': image_url,
                'subscribed_at': '2025-04-09T18:00:00Z'  # Optionally add a timestamp
            }
        )
        flash(f"Subscribed to '{title}' by {artist} successfully!")
    except Exception as e:
        flash("Error subscribing: " + str(e))

    return redirect(url_for('main'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    # Check that the user is logged in
    user = session.get('user')
    if not user:
        flash("Please log in first.")
        return redirect(url_for('login'))

    # Retrieve the song title from the form
    song_title = request.form.get('song_title')

    try:
        # Delete the subscription record from the Subscriptions table using the primary key.
        # Primary keys: 'user_email' and 'song_title'
        subscription_table.delete_item(
            Key={
                'user_email': user['email'],
                'song_title': song_title
            }
        )
        flash(f"Unsubscribed from '{song_title}' successfully!")
    except Exception as e:
        flash("Error unsubscribing: " + str(e))

    return redirect(url_for('main'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)