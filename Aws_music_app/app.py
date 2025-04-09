from flask import Flask, render_template, request, redirect, url_for, flash
import boto3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secure key

# Initialize DynamoDB resource and reference the Login table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login_table')


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')
        if user and user.get('password') == password:
            return redirect(url_for('main'))
        else:
            flash("Email or password is invalid")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
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
                    'username': username,
                    'password': password
                }
            )
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/main')
def main():
    return "Welcome to the Main Page!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
