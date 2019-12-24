# Built-In Modules
import os
from datetime import datetime, timedelta
import logging

# Local Modules
from octolytics.git_client import GitClient
from octolytics.badge_maker import BadgeMaker
from octolytics.mailer import Mailer
from octolytics.octodb import OctoDB

# 3rd Party Modules
from flask import Flask, render_template, request, url_for, redirect, make_response
from flask_dance.contrib.github import make_github_blueprint, github


# Create our logging
logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging.Logger('SERVER')
log.setLevel(30)
# Create our flask object
app = Flask(__name__, static_url_path = "", static_folder = "templates/static")
app.secret_key = "supersekrit"
# Github Info
blueprint = make_github_blueprint(
    client_id=os.environ['CLIENT_ID'],
    client_secret=os.environ['CLIENT_SECRET'],
)
app.register_blueprint(blueprint, url_prefix="/login")
# Create our octodb instance
octoDB = OctoDB()
# Create our git_client object
git_client = GitClient()
badge_maker = BadgeMaker()
mail_client = Mailer()


def main():
    """Entry point. Parse any args"""
    # TODO: Check directory "./temp/" exists
    # if app.config['DEBUG']:
    #     app.config['DEBUG'] = True
    # This has to set env FLASK_DEBUG=0/1
    app.run(ssl_context='adhoc', port=8080)


@app.route("/", methods=['GET'])
def index():
    """This is our front page"""
    if github.authorized:
        return redirect('/dashboard')
    return render_template('index.html')


@app.route("/dashboard", methods=['GET'])
def dashboard():
    """This is for displaying the dashboard"""
    # Check if our user is authorized and working
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)

    # Get the username and password
    resp = resp.json()
    username = resp['login']
    email = resp['email']

    # Get our users data, if they don't have any data create it
    try:
        user_data = octoDB.query_user(username)
        if not user_data:
            user_data = octoDB.create_user(username, email)
            if user_data is False:
                raise Exception(f"DB Error updating user {username}")
    except Exception as e:
        logging.warning(f"Something went wrong when getting data for {username}.\nException: {e}")

    kwargs = request.args.get('kwargs')
    return render_template('dashboard.html', user_data=user_data, kwargs=kwargs)


@app.route("/login", methods=['GET'])
def login():
    """This is for logging in"""
    # If not authorized, do the dance
    if not github.authorized:
        return redirect(url_for("github.login"))

    # Sanity check and then display dashboard
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)
    return redirect('/dashboard')


@app.route("/add_alias", methods=['POST'])
def add_alias():
    """This is for adding alias"""
    # If not authorized
    if not github.authorized:
        return render_template('error.html', status_code=487)
    # Get the user and pull up their DB info
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)
    resp = resp.json()
    username = resp['login']

    # Get our users data, if they don't have any data create it
    try:
        user_data = octoDB.query_user(username)
        if not user_data:
            raise Exception("User not found")

        # Create a random number and email it to the user
        user_data = mail_client.send_code(resp['email'], user_data)
        octoDB.update_user(username, user_data)
    except Exception as e:
        logging.warning(f"Something went wrong when adding alias for {username}\nException: {e}")
        return render_template('error.html', status_code=505)

    kwargs = "alias_requested"
    return redirect(f"/dashboard?kwargs={kwargs}")


@app.route("/confirm_alias", methods=['GET'])
def confirm_alias():
    """Endpoint to confirm alias is valid"""
    # If not authorized
    if not github.authorized:
        return render_template('error.html', status_code=487)
    # Get the user and pull up their DB info
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)
    resp = resp.json()
    username = resp['login']
    # Load in their DB info and confirm
    try:
        user_data = octoDB.query_user(username)
        if not user_data:
            raise Exception("User not found")
        # Confirm the alias is valid, -1 is the default code
        unconfirmed_code = request.args.get('code', 0)
        unconfirmed_username = request.args.get('username')
        user_data = octoDB.query_user(username)
        request_time = user_data['sessions']['email_code'][1]
        valid_time = True if request_time > (datetime.now() - timedelta(minutes=30)) else False
        if valid_time and \
                unconfirmed_code == user_data['sessions']['email_code'][0] and \
                unconfirmed_username == user_data['username']:
            # Then add the alias and return to dashboard
            user_data['alias'].append(request.args.get('email'))
            # Add a cookie to indicate the new alias
            octoDB.update_user(username, user_data)
            kwargs = "new_alias"
            return redirect(f"/dashboard?kwargs={kwargs}")

    except Exception as e:
        logging.warning(f"Something went wrong when confirming alias for {username}\nException: {e}")
        return render_template('error.html', status_code=505)

    return redirect('/dashboard')


@app.route("/sync_repos", methods=['GET'])
def sync_repos():
    """Sync our authenticaed user"""
    # Get their repo information
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)
    resp = resp.json()
    username = resp['login']
    try:
        # Add/update database
        user_data = octoDB.query_user(username)
        if not user_data:
            raise Exception("No user found")
        # TODO: Add timeout per user
        # Update a users data:
        user_data['repo_data'] = git_client.get_all_lines(user_data['alias'], user_data['repos'])
        octoDB.update_user(username, user_data)
        return redirect('/dashboard')
    except Exception as e:
        logging.warning(f"Something went wrong when syncing {username}\nException: {e}")
        return render_template('error.html', status_code=487)


@app.route("/get_repos", methods=['GET'])
def get_repos():
    """Endpoint to get all repos and store in DB"""
    # Get our users repos and check
    user_resp = github.get("/user")
    resp = github.get("/user/repos")
    if not resp.ok:
        render_template('error.html', status_code=300)

    # Convert to readable
    user_resp = user_resp.json()
    username = user_resp['login']
    resp = resp.json()
    # Loop and and save
    repos = {}
    for repo in resp:
        repos[repo['name']] = repo['git_url']

    # Add/update database
    try:
        user_data = octoDB.query_user(username)
        if not user_data:
            raise Exception("Count not find user")
        user_data['repos'] = repos
        octoDB.update_user(username, user_data)
    except Exception as e:
        logging.warning(f"Something went wrong when syncing repos for {username}\nException: {e}")
        render_template('error.html', status_code=505)

    return redirect('/dashboard')


@app.route("/badge", methods=['GET'])
def badge():
    """Endpoint to badge for a certain user in our repo"""
    # Extract the user from the url
    username = request.args.get('username')
    file_type = request.args.get('file_type')

    # Find the user in our database, if not return error badge
    try:
        user_data = octoDB.query_user(username)
        if user_data and user_data.get('repo_data', {}).get('ALL', None):
            # Check if we already have the badge
            if user_data['badges'].get(file_type):
                # If we already updated the data recently return cache
                valid_time =  True if user_data['badges'].get(file_type)[1] > (datetime.now() - timedelta(days=10)) else False
                if valid_time:
                    return user_data['badges'][file_type]
            # Make, save and return the badge
            user_badge = badge_maker.make_badge(user_data.get('repo_data').get('ALL'), file_type)
            user_data['badges'][file_type] = (user_badge, datetime.now())
            octoDB.update_user(username, user_data)
            return user_badge
        else:
            # TODO: Change this to error badge image
            return redirect('/')
    except Exception as e:
        logging.warning(f"Error getting the badge for {username}\n{e}")
        render_template('/')