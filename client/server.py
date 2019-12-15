# Built-In Modules
import os

# Local Modules
from client.git_client import GitClient
from client.badge_maker import BadgeMaker

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
}
# Create our git_client object
git_client = GitClient()
badge_maker = BadgeMaker()

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
    
    return render_template('dashboard.html',
                            data=data,)


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
            data['alias'].append(request.form['alias'])
            db_client.update_one({'username': username}, {"$set": data}, upsert=False)
        except:
            print(f"[DB]: Something went wrong when getting data for {username}")
            return render_template('error.html', status_code=487)
    else:
        print(f"[DB]: Something went wrong when adding alias for {username}")
        return render_template('error.html', status_code=487)

    # Sanity check and then display dashboard
    resp = github.get("/user")
    if not resp.ok:
        render_template('error.html', status_code=300)
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
        # Make and return the badge
        user_badge = badge_maker.make_badge(user_data.get('repo_data').get('ALL'), file_type)
        return user_badge
    else:
        # TODO: Change this to error badge image
        return redirect('/')

if __name__ == "__main__":
    app.run(ssl_context='adhoc')
