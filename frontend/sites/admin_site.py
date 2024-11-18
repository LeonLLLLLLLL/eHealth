from flask import Blueprint, render_template, request, redirect, url_for
import requests

admin_site = Blueprint('admin_site', __name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Base URL for the FastAPI server

@admin_site.route('/')
def admin_panel():
    """
    Render the admin panel page.
    """
    return render_template('admin_panel.html')

@admin_site.route('/add_user', methods=['POST'])
def add_user():
    """
    Handle form submission for adding a new user.
    """
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    roles = request.form.getlist('roles')  # Get roles as a list

    # Payload for the FastAPI add user endpoint
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "roles": roles
    }

    try:
        # Send POST request to FastAPI add user endpoint
        response = requests.post(f"{FASTAPI_BASE_URL}/register", json=user_data)
        response.raise_for_status()
        return redirect(url_for('admin_site.admin_panel'))
    except requests.RequestException as e:
        return render_template('error.html', message=f"Connection error: {str(e)}")
