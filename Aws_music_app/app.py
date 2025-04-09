from flask import Flask, render_template, request, redirect, url_for, flash,session
import boto3

app = Flask(__name__)
app.secret_key = 'AdocziPo+7Kqivi6rlIHkfCc+AW0DkqrRtluWyT0'  # Set a secure key

# Initialize DynamoDB resource and reference the Login table
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login_table')


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
    user = session.get('user_name')
    print("Session user in /main:", user)  # Debug print
    if not user:
        flash("Please log in first")
        return redirect(url_for('login'))
    return render_template('main.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)