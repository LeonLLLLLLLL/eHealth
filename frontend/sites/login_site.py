from flask import Blueprint, render_template, request, redirect, session, url_for
import requests
from jose import jwt, JWTError

login_site = Blueprint('login_site', __name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Base URL for the FastAPI server
SECRET_KEY = "your_secret_key"  # Replace with the same secret used in the FastAPI app
ALGORITHM = "HS256"  # Same algorithm as used in FastAPI

@login_site.route('/')
def login_page():
    """
    Render the login page.
    """
    if 'access_token' in session:
        print("go to admin ")
        decoded_token = jwt.decode(
            session['access_token'], SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_roles = decoded_token.get("roles", ["user"])
        user_role = user_roles[0]
        if user_role == "admin":
            return redirect(url_for('admin_site.admin_panel'))
    return render_template('login.html')

@login_site.route('/process', methods=['POST'])
def login_process():
    """
    Process login form and communicate with FastAPI for authentication.
    """
    username = request.form['username']
    password = request.form['password']

    # Payload for the FastAPI token endpoint
    login_data = {
        "username": username,
        "password": password
    }

    try:
        # Send POST request to FastAPI token endpoint
        response = requests.post(f"{FASTAPI_BASE_URL}/token", data=login_data)
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException as e:
        return render_template('error.html', message=f"Connection error: {str(e)}")

    # Handle FastAPI response
    if 'access_token' in response_data:
        # Store the JWT token in session
        session['access_token'] = response_data['access_token']

        try:
            # Decode the JWT token to extract roles
            decoded_token = jwt.decode(
                response_data['access_token'], SECRET_KEY, algorithms=[ALGORITHM]
            )
            user_roles = decoded_token.get("roles", ["user"])
            user_role = user_roles[0]  # Assume the first role is the primary role

            # Determine redirect target based on role
            if user_role == "admin":
                return redirect(url_for('admin_site.admin_panel'))
            elif user_role == "macro_pathologist":
                return redirect("/macro_case_panel")
            else:
                return redirect("/")
        except JWTError:
            return render_template('error.html', message="Failed to decode authentication token.")

    else:
        # Login failed
        return render_template('error.html', message="Invalid username or password. Please try again.")
