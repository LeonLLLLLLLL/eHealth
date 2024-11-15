from flask import Blueprint, render_template, request
import requests  # To send requests to the FastAPI server

login_site = Blueprint('login_site', __name__)

# Flask route for the login page
@login_site.route('/')
def login_page():
    return render_template('login.html')

# Flask route to process login and communicate with the FastAPI REST API
@login_site.route('/process', methods=['POST'])
def login_process():
    # Get username and password from the form
    username = request.form['username']
    password = request.form['password']

    # Data to send to the FastAPI endpoint
    login_data = {
        "username": username,
        "password": password
    }

    # URL of the FastAPI login endpoint
    fastapi_url = "http://127.0.0.1:8000/login"

    # Send POST request to the FastAPI server
    try:
        response = requests.post(fastapi_url, json=login_data)
        response_data = response.json()
    except requests.RequestException as e:
        return f"<h1>Error!</h1><p>Unable to connect to the authentication server: {str(e)}</p>"

    # Process the response from FastAPI
    if response_data.get("success"):
        return f"<h1>Welcome, {username}!</h1><p>Login Successful.</p>"
    else:
        return "<h1>Login Failed!</h1><p>Invalid username or password. <a href='/'>Try again</a></p>"
