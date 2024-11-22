from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import requests
from jose import jwt, JWTError

macro_case_panel = Blueprint('macro_case_panel', __name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Base URL for the FastAPI server
SECRET_KEY = "your_secret_key"  # Replace with the same secret used in the FastAPI app
ALGORITHM = "HS256"  # Same algorithm as used in FastAPI

@macro_case_panel.route('/')
def macro_case_page():
    """
    Render the macro case panel page.
    Accessible by users with "admin" or "macro_pathologist" roles.
    """
    if 'access_token' not in session:
        return redirect(url_for('login_site.login_page'))  # Redirect to login if not authenticated
    try:
        # Decode the token
        decoded_token = jwt.decode(
            session['access_token'], SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_roles = decoded_token.get("roles", ["user"])
        user_role = user_roles[0]

        # Check if the role is allowed
        if user_role not in ["admin", "macro_pathologist"]:
            session.pop('access_token', None)
            return redirect(url_for('login_site.login_page'))

        # Extract username for display
        username = decoded_token.get("sub")
    except JWTError:
        return redirect(url_for('login_site.login_page'))  # Redirect on token decode failure

    # Render the macro case panel page with the username
    return render_template('macro_case_panel.html', user_name=username)

@macro_case_panel.route('/upload', methods=['POST'])
def upload_image():
    """
    Handle form submission for uploading images to a specific case.
    """
    if 'access_token' not in session:
        return redirect(url_for('login_site.login_page'))  # Redirect to login if not authenticated

    case_name = request.form['caseName']
    files = request.files.getlist('images')

    try:
        # Send each file to the FastAPI upload endpoint
        for file in files:
            headers = {"Authorization": f"Bearer {session['access_token']}"}
            response = requests.post(
                f"{FASTAPI_BASE_URL}/cases/{case_name}/upload-image",
                files={"file": (file.filename, file.stream, file.content_type)},
                headers=headers
            )
            response.raise_for_status()

        flash(f"Images successfully uploaded to case '{case_name}'!", "success")
        return redirect(url_for('macro_case_panel.macro_case_page'))

    except requests.RequestException as e:
        flash(f"Error uploading images: {str(e)}", "danger")
        return redirect(url_for('macro_case_panel.macro_case_page'))

@macro_case_panel.route('/logout', methods=['POST'])
def logout():
    """
    Logs out the user by invalidating their token.
    """
    session.pop('access_token', None)  # Remove the token from the session
    return redirect(url_for('login_site.login_page'))  # Redirect to the login page
