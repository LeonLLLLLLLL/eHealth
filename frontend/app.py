from flask import Flask
from flask_session import Session
from sites.login_site import login_site
from sites.other_site import other_site
from sites.admin_site import admin_site
from sites.macro_case_panel import macro_case_panel

app = Flask(__name__)

# Configure the Flask app
app.secret_key = "your_secret_key"  # Replace with a strong, secure key
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in the file system
app.config["SESSION_PERMANENT"] = False    # Make sessions non-permanent (for security)

# Initialize session handling
Session(app)

# Register Blueprints for modular site management
app.register_blueprint(login_site, url_prefix='/login')
app.register_blueprint(other_site, url_prefix='/other')
app.register_blueprint(admin_site, url_prefix='/admin_panel')
app.register_blueprint(macro_case_panel, url_prefix='/macro_case_panel')

if __name__ == '__main__':
    app.run(debug=True)
