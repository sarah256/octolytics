# Built-In Modules
import os
from datetime import datetime, timedelta

# Local Modules
from octoserver.git_client import GitClient
from octoserver.badge_maker import BadgeMaker
from octoserver.mailer import Mailer
from octoserver.config import config

# 3rd Party Modules
from flask import Flask, render_template, request, url_for, redirect
from flask_dance.contrib.github import make_github_blueprint, github
from pymongo import MongoClient

# Create our flask object
app = Flask(__name__, static_url_path = "", static_folder = "templates/static")
app.secret_key = "supersekrit"
# Github Info
blueprint = make_github_blueprint(
    client_id=os.environ['CLIENT_ID'],
    client_secret=os.environ['CLIENT_SECRET'],
)
app.register_blueprint(blueprint, url_prefix="/login")
# Create our database data
DB_NAME = 'woof-are-you'
DB_HOST = 'ds063160.mlab.com'
DB_PORT = 63160
DB_USER = os.environ['MONGO_USER']
DB_PASS = os.environ['MONGO_PASS']
connection = MongoClient(DB_HOST, DB_PORT, retryWrites=False)
db = connection[DB_NAME]
db.authenticate(DB_USER, DB_PASS)
db_client = db.octolytics_data
DATABASE_SCHEMA = {
    'username': None,
    'alias': None,
    'repos': None,
    # repo: { repo_name, repo_url }
    'repo_data': None,
    # repo_data: {'judymoses.github.io': {'.py': 50}}
    'badges': {},
    # badges: {'.py': svg_file}
    'sessions': {
        'email_code': (-1, datetime(1, 1, 1))
        # email_code: (code, datetime)
    }
}
# Create our git_client object
git_client = GitClient()
badge_maker = BadgeMaker()
mail_client = Mailer()


def main():
    """Entry point. Parse any args"""
    # import pdb; pdb.set_trace()
    if config['debug']:
        app.debug=True


    app.run(ssl_context='adhoc')

@app.route("/", methods=['GET'])
def index():
    """This is our front page"""
    if github.authorized:
        return redirect('/dashboard')
    return render_template('index.html')


@app.route("/dashboard", methods=['GET'])
def dashboard():
    """This is for displaying the dashboard"""
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")

    if not resp.ok:
        render_template('error.html', status_code=300)
    resp = resp.json()
    username = resp['login']
    # Get our users data, if they don't have any data create it
    if db_client.find_one({"username": username}):
        # Update a users data
        try:
            data = db_client.find_one({"username": username})
        except:
            print(f"[DB]: Something went wrong when getting data for {username}")
            return render_template('error.html', status_code=487)
    else:
        # Create the user document
        try:
            data = DATABASE_SCHEMA
            data['username'] = username
            data['alias'] = [resp['email']]
            db_client.insert_one(data)
        except:
            print(f"[DB]: Something went wrong when updating {username}")
            return render_template('error.html', status_code=487)

    kwargs = request.args.get('kwargs', {})
    return render_template('dashboard.html',
                            data=data, kwargs=kwargs)


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
    # Load in their DB info
    if db_client.find_one({"username": username}):
        # Update a users data
        try:
            data = db_client.find_one({"username": username})
            # Create a random number and email it to the user
            data = mail_client.send_code(resp['email'], data)
            db_client.update_one({'username': username}, {"$set": data}, upsert=False)
        except:
            print(f"[DB]: Something went wrong when adding alias for {username}")
            return render_template('error.html', status_code=487)
    else:
        print(f"[DB]: Something went wrong when adding alias for {username}")
        return render_template('error.html', status_code=487)
    kwargs = {"alias_requested": True}
    return redirect(f"/dashboard?kwargs={kwargs}")


@app.route("/confirm_alias", methods=['POST'])
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
    user_data = db_client.find_one({"username": username})
    if user_data and request.args.get('email'):
        try:
            # Confirm the alias is valid, -1 is the default code
            unconfirmed_code = request.args.get('code', 0)
            unconfirmed_username = request.args.get('username')
            user_data = db_client.find_one({"username": username})
            request_time = user_data['sessions']['email_code'][1]
            valid_time = True if request_time > (datetime.now() - timedelta(minutes=30)) else False
            if valid_time and \
                    unconfirmed_code == user_data['sessions']['email_code'][0] and \
                    unconfirmed_username == user_data['username']:
                # Then add the alias and return to dashboard
                user_data['alias'].append(request.args.get('email'))
                # Add a cookie to indicate the new alias
                db_client.update_one({'username': username}, {"$set": user_data}, upsert=False)
                kwargs = {'new_alias': request.args.get('email')}
                return redirect(f"/dashboard?kwargs={kwargs}")
        except:
            print(f"[DB]: Something went wrong when confirming alias {username}")
            return render_template('error.html', status_code=487)
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

    # Add/update database
    user_data = db_client.find_one({"username": username})
    if not user_data:
        # Throw an error
        print(f"[FLASK]: This should not happen. User: {username}")
        render_template('error.html', status_code=500)
    # TODO: Add timeout per user
    # Update a users data
    try:
        user_data['repo_data'] = git_client.get_all_lines(user_data['alias'], user_data['repos'])
        db_client.update_one({'username': username}, {"$set": user_data}, upsert=False)
        return redirect('/dashboard')
    except Exception as e:
        print(f"[GITCLIENT]: Something went wrong when syncing {username}\nException: {e}")
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
    to_insert = db_client.find_one({"username": username})
    if to_insert:
        # Update a users data
        try:
            to_insert['repos'] = repos
            db_client.update_one({'username': username}, {"$set": to_insert}, upsert=False)
        except:
            print(f"[DB]: Something went wrong when updating {username}")
            return render_template('error.html', status_code=487)
    else:
        # Create the user document
        print(f"[FLASK]: This should not happen. User: {username}")
        render_template('error.html', status_code=500)
    return redirect('/dashboard')


@app.route("/badge", methods=['GET'])
def badge():
    """Endpoint to badge for a certain user in our repo"""
    # Extract the user from the url
    username = request.args.get('username')
    file_type = request.args.get('file_type')

    # Find the user in our database, if not return error badge
    user_data = db_client.find_one({"username": username})
    if user_data and user_data.get('repo_data', {}).get('ALL', None):
        # Check if we already have the badge
        if user_data['badges'].get(file_type):
            return user_data['badges'][file_type]
        # TODO: Check the timestamp it was updated
        # Make, save and return the badge
        user_badge = badge_maker.make_badge(user_data.get('repo_data').get('ALL'), file_type)
        user_data['badges'][file_type] = user_badge
        db_client.update_one({'username': username}, {"$set": user_data}, upsert=False)
        return user_badge
    else:
        # TODO: Change this to error badge image
        return redirect('/')
