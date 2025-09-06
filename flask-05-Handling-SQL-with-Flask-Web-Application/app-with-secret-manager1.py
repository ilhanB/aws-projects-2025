import boto3
from botocore.exceptions import ClientError
from flask import Flask, request, render_template
from flask_mysqldb import MySQL
import json

app = Flask(__name__)

# Function to retrieve secrets from AWS Secrets Manager
def get_secret():
    secret_name = "aws-flask-demo-credentials"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Parse the secret string as JSON
    secret = json.loads(get_secret_value_response['SecretString'])
    
    return secret

# Retrieve the secrets
secrets = get_secret()

# Configure MySQL database
app.config['MYSQL_HOST'] = secrets['host']
app.config['MYSQL_USER'] = secrets['username']
app.config['MYSQL_PASSWORD'] = secrets['password']
app.config['MYSQL_DB'] = secrets['dbname']
app.config['MYSQL_PORT'] = int(secrets['port'])
mysql = MySQL(app)

# Initialize database: create users table and sample data
def init_db():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("DROP TABLE IF EXISTS users;")
        cur.execute("""
            CREATE TABLE users (
                username VARCHAR(50) NOT NULL PRIMARY KEY,
                email VARCHAR(50)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        cur.executemany("""
            INSERT INTO users (username, email) VALUES (%s, %s);
        """, [
            ("dora", "dora@amazon.com"),
            ("cansın", "cansın@google.com"),
            ("sencer", "sencer@bmw.com"),
            ("uras", "uras@mercedes.com"),
            ("ares", "ares@porche.com")
        ])
        mysql.connection.commit()
        cur.close()

# Call init_db only once (comment out after first run)
# init_db()

# Function to find emails by username keyword
def find_emails(keyword):
    cur = mysql.connection.cursor()
    query = "SELECT username, email FROM users WHERE username LIKE %s;"
    cur.execute(query, ('%' + keyword + '%',))
    results = cur.fetchall()
    cur.close()
    if not results:
        results = [('Not found.', 'Not Found.')]
    return results

# Function to insert a new user/email
def insert_email(name, email):
    if not name or not email:
        return 'Username or email cannot be empty!!'
    
    cur = mysql.connection.cursor()
    # Check if user exists
    cur.execute("SELECT * FROM users WHERE username=%s;", (name,))
    exists = cur.fetchone()
    if exists:
        cur.close()
        return f'User {name} already exists.'
    
    # Insert new user
    cur.execute("INSERT INTO users (username, email) VALUES (%s, %s);", (name, email))
    mysql.connection.commit()
    cur.close()
    return f'User {name} and {email} have been added successfully'

# Route to search emails
@app.route('/', methods=['GET', 'POST'])
def emails():
    if request.method == 'POST':
        user_name = request.form['user_keyword']
        user_emails = find_emails(user_name)
        return render_template('emails.html', name_emails=user_emails, keyword=user_name, show_result=True)
    else:
        return render_template('emails.html', show_result=False)

# Route to add new email
@app.route('/add', methods=['GET', 'POST'])
def add_email():
    if request.method == 'POST':
        user_name = request.form['username']
        user_email = request.form['useremail']
        result = insert_email(user_name, user_email)
        return render_template('add-email.html', result_html=result, show_result=True)
    else:
        return render_template('add-email.html', show_result=False)

# Add a statement to run the Flask application which can be reached from any host on port 80.
if __name__ == '__main__':
   # app.run(debug=True)
    app.run(host='0.0.0.0', port=80)
