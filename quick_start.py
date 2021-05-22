# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import os
from flask import Flask, render_template_string, session, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, current_user
import sys
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

from werkzeug.utils import redirect

URL = "http://localhost:5000"

FB_CLIENT_ID = "980020299425667"
FB_CLIENT_SECRET = "efa8603ffd7d47225c69910f4a60fc54"

FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

FB_SCOPE = ["email"]

# This allows us to use a plain HTTP callback
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///quickstart_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Flask-User QuickStart App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False      # Disable email authentication
    USER_ENABLE_USERNAME = True    # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = False    # Simplify register form


def create_app():
    """ Flask application factory """
    
    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        email_confirmed_at = db.Column(db.DateTime())

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Create all database tables
    db.create_all()

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        """ mark = User(username= 'mark', password= 'asdfasdf')
        user_manager
        db
        import code; code.interact(local=dict(globals(), **locals()))
        print(mark, file=sys.stderr)
        print(current_user.is_active, file=sys.stderr) """
        # String-based templates
        sss = None
        if current_user.is_active:
            sss = ""
        else:
            sss = """<p><a href={{ url_for('user.register') }}>Register</a></p>
                <p><a href={{ url_for('user.login') }}>Sign in</a></p>
                <p><a href="/fb-login">Login with Facebook</a></p>
                """
        return render_template_string(f"""
            {{% extends "flask_user_layout.html" %}}
            {{% block content %}}
                <h2>Home page</h2>
                {sss}
                <p><a href={{{{ url_for('home_page') }}}}>Home page</a> (accessible to anyone)</p>
                <p><a href={{{{ url_for('member_page') }}}}>Member page</a> (login required)</p>
                <p><a href={{{{ url_for('user.logout') }}}}>Sign out</a></p>
            {{% endblock %}}
            """)

    # The Members page is only accessible to authenticated users via the @login_required decorator
    @app.route('/members')
    def member_page():
        if current_user.is_active or dict(session).get('username', None):
            # String-based templates
            return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>Members page</h2>
                    <h3>Hello {{current_user.username or dict(session).get('username')}}</h3>
                    <h3>Avatar <img src="{{session['picture_url']}}"></h3>
                    <p><a href={{ url_for('home_page') }}>Home page</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('member_page') }}>Member page</a> (login required)</p>
                    <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
                {% endblock %}
                """)
        return redirect(url_for('home_page'))

    @app.route("/fb-login")
    def fb_login():
        facebook = requests_oauthlib.OAuth2Session(
            FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE
        )
        authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

        return redirect(authorization_url)

    @app.route("/fb-callback")
    def db_callback():
        facebook = requests_oauthlib.OAuth2Session(
            FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback"
        )

        # we need to apply a fix for Facebook here
        facebook = facebook_compliance_fix(facebook)

        facebook.fetch_token(
            FB_TOKEN_URL,
            client_secret=FB_CLIENT_SECRET,
            authorization_response=request.url,
        )

        # Fetch a protected resource, i.e. user profile, via Graph API

        facebook_user_data = facebook.get(
            "https://graph.facebook.com/me?fields=id,name,email,picture{url}"
        ).json()

        email = facebook_user_data["email"]
        name = facebook_user_data["name"]
        picture_url = facebook_user_data.get("picture", {}).get("data", {}).get("url")

        session['username'] = name
        session['picture_url'] = picture_url

        user_info = f"""
        User information: <br>
        Name: {name} <br>
        Email: {email} <br>
        Avatar <img src="{picture_url}"> <br>
        <a href="/">Home</a>
        """
        return redirect(url_for('home_page'))

    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)