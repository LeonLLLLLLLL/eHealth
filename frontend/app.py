from flask import Flask
from sites.login_site import login_site
from sites.other_site import other_site
from sites.admin_site import admin_site  # Import the new admin_site

app = Flask(__name__)

# Register Blueprints for modular site management
app.register_blueprint(login_site, url_prefix='/login')
app.register_blueprint(other_site, url_prefix='/other')
app.register_blueprint(admin_site, url_prefix='/admin_panel')

if __name__ == '__main__':
    app.run(debug=True)
