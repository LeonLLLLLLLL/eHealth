from flask import Blueprint, render_template

other_site = Blueprint('other_site', __name__)

@other_site.route('/')
def other_page():
    return "<h1>Welcome to the Other Site!</h1><p>Future content will go here.</p>"
