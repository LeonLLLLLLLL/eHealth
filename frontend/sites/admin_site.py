from flask import Blueprint, render_template, request, redirect, url_for, session
import requests
from jose import jwt, JWTError

admin_site = Blueprint('admin_site', __name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Base URL for the FastAPI server
SECRET_KEY = "your_secret_key"  # Replace with the same secret used in the FastAPI app
ALGORITHM = "HS256"  # Same algorithm as used in FastAPI

@admin_site.route('/')
def admin_panel():
    """
    Render the admin panel page.
    """
    if 'access_token' not in session:
        return redirect(url_for('login_site.login_page'))  # Redirect to login if not authenticated
    try:
        decoded_token = jwt.decode(
            session['access_token'], SECRET_KEY, algorithms=[ALGORITHM]
        )
        username = decoded_token.get("sub")
    except JWTError:
        return redirect(url_for('login_site.login_page'))  # Redirect on token decode failure

    return render_template('admin_panel.html', admin_name=username)

@admin_site.route('/add_user', methods=['POST'])
def add_user():
    """
    Handle form submission for adding a new user.
    """
    if 'access_token' not in session:
        return redirect(url_for('login_site.login_page'))  # Redirect to login if not authenticated

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
        # Send POST request to FastAPI register endpoint with the token
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        response = requests.post(f"{FASTAPI_BASE_URL}/register", json=user_data, headers=headers)
        response.raise_for_status()
        return redirect(url_for('admin_site.admin_panel'))
    except requests.RequestException as e:
        return render_template('error.html', message=f"Connection error: {str(e)}")
    except KeyError:
        return render_template('error.html', message="Authentication failed. Please log in again.")

@admin_site.route('/add_case', methods=['POST'])
def add_case():
    """
    Handle form submission for creating a new case.
    """
    if 'access_token' not in session:
        return redirect(url_for('login_site.login_page'))  # Redirect to login if not authenticated

    case_name = request.form['caseName']
    description = request.form['description']

    # Payload for the FastAPI create case endpoint
    case_data = {
        "caseName": case_name,
        "description": description
    }

    try:
        # Send POST request to FastAPI create case endpoint with the token
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        response = requests.post(f"{FASTAPI_BASE_URL}/cases", json=case_data, headers=headers)
        response.raise_for_status()
        return redirect(url_for('admin_site.admin_panel'))
    except requests.RequestException as e:
        return render_template('error.html', message=f"Connection error: {str(e)}")
    except KeyError:
        return render_template('error.html', message="Authentication failed. Please log in again.")

@admin_site.route('/logout', methods=['POST'])
def logout():
    """
    Logs out the admin by invalidating their token.
    """
    session.pop('access_token', None)  # Remove the token from the session
    return redirect(url_for('login_site.login_page'))
