from flask import Blueprint, render_template, request, redirect
import requests

login_site = Blueprint('login_site', __name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Base URL for the FastAPI server

@login_site.route('/')
def login_page():
    """
    Render the login page.
    """
    return render_template('login.html')

@login_site.route('/process', methods=['POST'])
def login_process():
    """
    Process login form and communicate with FastAPI for authentication.
    """
    username = request.form['username']
    password = request.form['password']

    # Payload for the FastAPI login endpoint
    login_data = {
        "username": username,
        "password": password
    }

    try:
        # Send POST request to FastAPI login endpoint
        response = requests.post(f"{FASTAPI_BASE_URL}/login", json=login_data)
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException as e:
        return render_template('error.html', message=f"Connection error: {str(e)}")

    # Handle FastAPI response
    if response_data.get("success"):
        user_role = response_data.get("roles", ["user"])[0]  # Assume first role in roles list

        # Determine redirect target based on role
        if user_role == "admin":
            return redirect("/admin_panel")  # Added return
        elif user_role == "pathologist":
            return redirect("/case_panel")  # Added return
        else:
            return redirect("./")  # Added return

    else:
        # Login failed
        return render_template('error.html', message="Invalid username or password. Please try again.")
